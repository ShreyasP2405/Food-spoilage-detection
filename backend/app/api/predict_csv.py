"""
Bulk-prediction endpoint: accepts a CSV upload, predicts RSL + traffic light
status for every row, returns a JSON summary plus per-row predictions and
an annotated CSV the frontend can download.

Strict schema: required columns are the seven model features.
Optional columns (timestamp, batch_id, ripeness_stage_1to7) are passed through
unchanged. Any extra columns are echoed back too.
"""
from __future__ import annotations

import io
import logging
from typing import Any

import numpy as np
import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import settings
from app.ml import model as ml_model
from app.ml.preprocess import FEATURE_ORDER, clamp_features
from app.ml.traffic_light import classify

router = APIRouter()
log = logging.getLogger(__name__)

REQUIRED_COLUMNS = [
    "temp_c",
    "humidity_pct",
    "co2_ppm",
    "ethylene_ppm",
    "methane_ppm",
    "hours_since_harvest",
    "ripeness_estimate",
]

# Common alternate names mapped to required ones (column-rename only, no inference)
ALIAS_MAP = {
    "DHT22_temperature_C": "temp_c",
    "DHT22_humidity_percent": "humidity_pct",
    "MQ135_co2_ppm": "co2_ppm",
    "MQ135_ethylene_ppm": "ethylene_ppm",
    "MQ4_methane_ppm": "methane_ppm",
    "elapsed_hours": "hours_since_harvest",
    "ripeness_stage_1to7": "ripeness_estimate",
}

MAX_ROWS = 50_000


@router.post("/predict-csv")
async def predict_csv(file: UploadFile = File(...)) -> dict[str, Any]:
    if not file.filename or not file.filename.lower().endswith((".csv", ".txt")):
        raise HTTPException(status_code=400, detail="Please upload a .csv file.")

    raw = await file.read()
    if len(raw) == 0:
        raise HTTPException(status_code=400, detail="File is empty.")
    if len(raw) > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 50 MB).")

    try:
        df = pd.read_csv(io.BytesIO(raw))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {e}")

    if len(df) == 0:
        raise HTTPException(status_code=400, detail="CSV has no data rows.")
    if len(df) > MAX_ROWS:
        raise HTTPException(status_code=413, detail=f"Too many rows (max {MAX_ROWS}).")

    df = df.rename(columns={k: v for k, v in ALIAS_MAP.items() if k in df.columns})

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Missing required columns: {missing}. "
                f"Required (or aliases): {REQUIRED_COLUMNS}. "
                f"Aliases accepted: {list(ALIAS_MAP.keys())}."
            ),
        )

    for c in REQUIRED_COLUMNS:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    if df[REQUIRED_COLUMNS].isna().any().any():
        bad = df[df[REQUIRED_COLUMNS].isna().any(axis=1)].index.tolist()[:5]
        raise HTTPException(
            status_code=422,
            detail=f"Non-numeric or missing values in required columns. First bad row indices: {bad}",
        )

    bundle = ml_model.get_bundle()
    rsl_values: list[float] = []
    confidence_values: list[float] = []
    statuses: list[str] = []
    reasons: list[str] = []
    factor_counts: list[int] = []

    if bundle.kind == "lstm" and bundle.scaler is not None:
        feats_clamped = []
        for i in range(len(df)):
            row = {c: float(df.iloc[i][c]) for c in REQUIRED_COLUMNS}
            cleaned, _ = clamp_features(row)
            feats_clamped.append([cleaned[c] for c in FEATURE_ORDER])
        feats_arr = np.asarray(feats_clamped, dtype=np.float32)
        feats_scaled = bundle.scaler.transform(feats_arr)

        window = bundle.window
        if len(feats_scaled) < window:
            pad = np.repeat(feats_scaled[:1], window - len(feats_scaled), axis=0)
            padded = np.vstack([pad, feats_scaled])
        else:
            padded = feats_scaled

        seqs = []
        for i in range(len(df)):
            end = i + (window - len(feats_scaled)) if len(feats_scaled) < window else i + 1
            start = max(0, end - window)
            chunk = padded[start:end]
            if chunk.shape[0] < window:
                pad = np.repeat(chunk[:1], window - chunk.shape[0], axis=0)
                chunk = np.vstack([pad, chunk])
            seqs.append(chunk)
        X = np.asarray(seqs, dtype=np.float32)
        preds = bundle.model.predict(X, batch_size=512, verbose=0).flatten()
        for i, p in enumerate(preds):
            rsl = max(0.0, float(p))
            row = df.iloc[i]
            status, reason, factors = classify(
                rsl,
                temp_c=float(row["temp_c"]),
                humidity_pct=float(row["humidity_pct"]),
                co2_ppm=float(row["co2_ppm"]),
                methane_ppm=float(row["methane_ppm"]),
                ethylene_ppm=float(row["ethylene_ppm"]),
            )
            rsl_values.append(rsl)
            confidence_values.append(0.8)
            statuses.append(status)
            reasons.append(reason)
            factor_counts.append(len(factors))
    else:
        for i in range(len(df)):
            row_dict = {c: float(df.iloc[i][c]) for c in REQUIRED_COLUMNS}
            rsl, conf, _ = ml_model.predict_single(row_dict)
            rsl = max(0.0, rsl)
            row = df.iloc[i]
            status, reason, factors = classify(
                rsl,
                temp_c=float(row["temp_c"]),
                humidity_pct=float(row["humidity_pct"]),
                co2_ppm=float(row["co2_ppm"]),
                methane_ppm=float(row["methane_ppm"]),
                ethylene_ppm=float(row["ethylene_ppm"]),
            )
            rsl_values.append(rsl)
            confidence_values.append(float(conf))
            statuses.append(status)
            reasons.append(reason)
            factor_counts.append(len(factors))

    annotated = df.copy()
    annotated["predicted_rsl_days"] = [round(v, 3) for v in rsl_values]
    annotated["predicted_status"] = statuses
    annotated["prediction_confidence"] = [round(v, 3) for v in confidence_values]
    annotated["prediction_reason"] = reasons

    csv_buf = io.StringIO()
    annotated.to_csv(csv_buf, index=False)
    annotated_csv_text = csv_buf.getvalue()

    rows_payload = []
    preview_n = min(500, len(df))
    for i in range(preview_n):
        rows_payload.append({
            "row_index": int(i),
            "temp_c": float(df.iloc[i]["temp_c"]),
            "humidity_pct": float(df.iloc[i]["humidity_pct"]),
            "co2_ppm": float(df.iloc[i]["co2_ppm"]),
            "ethylene_ppm": float(df.iloc[i]["ethylene_ppm"]),
            "methane_ppm": float(df.iloc[i]["methane_ppm"]),
            "hours_since_harvest": float(df.iloc[i]["hours_since_harvest"]),
            "ripeness_estimate": int(df.iloc[i]["ripeness_estimate"]),
            "predicted_rsl_days": float(rsl_values[i]),
            "predicted_status": statuses[i],
            "prediction_reason": reasons[i],
            "prediction_confidence": float(confidence_values[i]),
            "contributing_factor_count": int(factor_counts[i]),
        })

    summary = {
        "filename": file.filename,
        "n_rows": int(len(df)),
        "n_preview_rows": int(preview_n),
        "model_kind": bundle.kind,
        "model_version": settings.model_version,
        "status_counts": {
            "green": int(sum(1 for s in statuses if s == "green")),
            "yellow": int(sum(1 for s in statuses if s == "yellow")),
            "red": int(sum(1 for s in statuses if s == "red")),
        },
        "rsl_stats": {
            "min": float(np.min(rsl_values)) if rsl_values else 0.0,
            "max": float(np.max(rsl_values)) if rsl_values else 0.0,
            "mean": float(np.mean(rsl_values)) if rsl_values else 0.0,
            "median": float(np.median(rsl_values)) if rsl_values else 0.0,
        },
        "rows": rows_payload,
        "annotated_csv": annotated_csv_text,
    }
    return summary
