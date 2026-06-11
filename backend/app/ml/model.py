"""
Model loader + prediction wrapper.

Tries to load LSTM if prefer_lstm and tensorflow available; falls back to RF.
If neither artifact exists, falls back to physics-based RSL estimate from the
simulator (so the API still works on a fresh repo).
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Literal, Optional

import joblib
import numpy as np

from app.core.config import settings
from app.ml.preprocess import FEATURE_ORDER, clamp_features, features_to_vector

log = logging.getLogger(__name__)


class ModelBundle:
    kind: Literal["lstm", "rf", "none"] = "none"
    model = None
    scaler = None
    metadata: dict = {}
    window: int = 1


_BUNDLE = ModelBundle()


def load_model() -> ModelBundle:
    """Called at app startup. Idempotent."""
    bundle = _BUNDLE
    artifacts = Path(settings.artifacts_dir)
    metadata_path = artifacts / "metadata.json"
    if metadata_path.exists():
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                bundle.metadata = json.load(f)
        except json.JSONDecodeError:
            bundle.metadata = {}

    scaler_path = artifacts / "scaler.joblib"
    if scaler_path.exists():
        bundle.scaler = joblib.load(scaler_path)

    lstm_path = artifacts / "lstm_model.keras"
    rf_path = artifacts / "rf_baseline.joblib"

    if settings.prefer_lstm and lstm_path.exists():
        try:
            import tensorflow as tf  # noqa
            bundle.model = tf.keras.models.load_model(lstm_path)
            bundle.kind = "lstm"
            bundle.window = 48
            log.info("Loaded LSTM model from %s", lstm_path)
            return bundle
        except Exception as e:
            log.warning("LSTM load failed (%s); falling back to RF.", e)

    if rf_path.exists():
        bundle.model = joblib.load(rf_path)
        bundle.kind = "rf"
        bundle.window = 1
        log.info("Loaded Random Forest model from %s", rf_path)
        return bundle

    bundle.kind = "none"
    log.warning("No trained model artifact found in %s; falling back to physics estimate.", artifacts)
    return bundle


def get_bundle() -> ModelBundle:
    return _BUNDLE


def _physics_fallback_rsl(features: dict) -> float:
    """When no model artifact exists, project shelf life with the simulator."""
    from ml.src.simulator import BananaSimulator
    sim = BananaSimulator(initial_ripeness=float(features["ripeness_estimate"]))
    sim.state.temp_c = float(features["temp_c"])
    sim.state.rh_pct = float(features["humidity_pct"])
    sim.state.co2_ppm = float(features["co2_ppm"])
    sim.state.ethylene_ppm = float(features["ethylene_ppm"])
    sim.state.methane_ppm = float(features["methane_ppm"])
    sim.state.t_hours = float(features["hours_since_harvest"])
    return float(sim.estimate_days_until_spoilage())


def predict_single(features: dict) -> tuple[float, float, list[str]]:
    """
    Returns (rsl_days, confidence, warnings).
    For single-sample requests with the LSTM, repeat the row into a window of 48
    (degraded but functional fallback). For real time-series prediction, use
    /api/predict-sequence.
    """
    cleaned, warns = clamp_features(features)
    bundle = _BUNDLE

    if bundle.kind == "none" or bundle.scaler is None:
        rsl = _physics_fallback_rsl(cleaned)
        return rsl, 0.5, warns + ["No trained model loaded — using physics fallback."]

    x = features_to_vector(cleaned).reshape(1, -1)
    x_scaled = bundle.scaler.transform(x)

    if bundle.kind == "rf":
        rsl = float(bundle.model.predict(x_scaled)[0])
        # crude confidence from std of tree predictions
        try:
            preds = np.stack([t.predict(x_scaled) for t in bundle.model.estimators_])
            std = float(preds.std(axis=0)[0])
            conf = max(0.1, min(0.99, 1.0 - std / 5.0))
        except Exception:
            conf = 0.7
        return rsl, conf, warns

    if bundle.kind == "lstm":
        seq = np.repeat(x_scaled[np.newaxis, :, :], bundle.window, axis=1)
        rsl = float(bundle.model.predict(seq, verbose=0).flatten()[0])
        return rsl, 0.6, warns + ["Single-sample LSTM call uses repeated-row window; prefer /predict-sequence."]

    return _physics_fallback_rsl(cleaned), 0.5, warns


def predict_sequence(rows: list[dict]) -> tuple[float, float, list[str]]:
    """Use the full sliding window if LSTM is loaded; otherwise predict on the last row."""
    cleaned_rows = []
    warns_all: list[str] = []
    for r in rows:
        c, w = clamp_features(r)
        cleaned_rows.append(c)
        warns_all.extend(w)

    bundle = _BUNDLE
    last = cleaned_rows[-1]

    if bundle.kind == "lstm" and bundle.scaler is not None:
        feats = np.asarray([[r[k] for k in FEATURE_ORDER] for r in cleaned_rows], dtype=np.float32)
        feats_s = bundle.scaler.transform(feats)
        if len(feats_s) < bundle.window:
            pad = np.repeat(feats_s[:1], bundle.window - len(feats_s), axis=0)
            feats_s = np.vstack([pad, feats_s])
        seq = feats_s[-bundle.window:][np.newaxis, :, :]
        rsl = float(bundle.model.predict(seq, verbose=0).flatten()[0])
        return rsl, 0.8, warns_all

    rsl, conf, w = predict_single(last)
    return rsl, conf, warns_all + w
