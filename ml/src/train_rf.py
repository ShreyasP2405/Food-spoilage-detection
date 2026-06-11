"""
Random Forest baseline trainer.

Flat features, no time. Honest baseline number for the report:
  features = [temp_c, humidity_pct, co2_ppm, ethylene_ppm, methane_ppm,
              hours_since_harvest, ripeness_estimate]
  target   = days_until_spoilage

Split is by batch_id (70/15/15) to prevent leakage between train/val/test.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "processed" / "banana_synthetic_v1.csv"
ARTIFACTS = Path(__file__).resolve().parents[1] / "artifacts"

FEATURES = [
    "temp_c",
    "humidity_pct",
    "co2_ppm",
    "ethylene_ppm",
    "methane_ppm",
    "hours_since_harvest",
    "ripeness_estimate",
]
TARGET = "days_until_spoilage"


def split_by_batch(df: pd.DataFrame, seed: int = 0) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    batches = df["batch_id"].unique()
    train_b, tmp_b = train_test_split(batches, test_size=0.30, random_state=seed)
    val_b, test_b = train_test_split(tmp_b, test_size=0.50, random_state=seed)
    return (
        df[df["batch_id"].isin(train_b)].copy(),
        df[df["batch_id"].isin(val_b)].copy(),
        df[df["batch_id"].isin(test_b)].copy(),
    )


def on_time_warning_rate(df: pd.DataFrame, y_pred: np.ndarray, lead_hours: float = 24.0) -> float:
    """For batches that ever spoil (status=red in ground truth),
    fraction where the model first predicted RSL <= 2 days at least lead_hours
    before the actual spoilage time. Computed per batch."""
    df = df.copy()
    df["pred_rsl"] = y_pred
    n_total = 0
    n_warned = 0
    for batch_id, g in df.groupby("batch_id"):
        g = g.sort_values("timestamp_h")
        spoil_idx = g.index[g["status"] == "red"]
        if len(spoil_idx) == 0:
            continue
        n_total += 1
        spoil_time = g.loc[spoil_idx[0], "timestamp_h"]
        warn_rows = g[g["pred_rsl"] <= 2.0]
        if len(warn_rows) > 0 and warn_rows.iloc[0]["timestamp_h"] <= spoil_time - lead_hours:
            n_warned += 1
    return n_warned / n_total if n_total else float("nan")


def false_alarm_rate(df: pd.DataFrame, y_pred: np.ndarray) -> float:
    df = df.copy()
    df["pred_rsl"] = y_pred
    green_rows = df[df["status"] == "green"]
    if len(green_rows) == 0:
        return float("nan")
    return float((green_rows["pred_rsl"] <= 2.0).mean())


def file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(DATA_PATH)
    train_df, val_df, test_df = split_by_batch(df)

    X_train, y_train = train_df[FEATURES].values, train_df[TARGET].values
    X_val, y_val = val_df[FEATURES].values, val_df[TARGET].values
    X_test, y_test = test_df[FEATURES].values, test_df[TARGET].values

    scaler = StandardScaler().fit(X_train)
    X_train_s, X_val_s, X_test_s = scaler.transform(X_train), scaler.transform(X_val), scaler.transform(X_test)

    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=20,
        min_samples_leaf=5,
        n_jobs=-1,
        random_state=0,
    )
    model.fit(X_train_s, y_train)

    y_pred_val = model.predict(X_val_s)
    y_pred_test = model.predict(X_test_s)

    metrics = {
        "model": "random_forest_baseline",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "data_sha256": file_sha(DATA_PATH),
        "feature_order": FEATURES,
        "target": TARGET,
        "val": {
            "mae_days": float(mean_absolute_error(y_val, y_pred_val)),
            "rmse_days": float(np.sqrt(mean_squared_error(y_val, y_pred_val))),
            "r2": float(r2_score(y_val, y_pred_val)),
        },
        "test": {
            "mae_days": float(mean_absolute_error(y_test, y_pred_test)),
            "rmse_days": float(np.sqrt(mean_squared_error(y_test, y_pred_test))),
            "r2": float(r2_score(y_test, y_pred_test)),
            "on_time_warning_rate_24h": float(on_time_warning_rate(test_df, y_pred_test)),
            "false_alarm_rate": float(false_alarm_rate(test_df, y_pred_test)),
        },
    }

    joblib.dump(model, ARTIFACTS / "rf_baseline.joblib")
    joblib.dump(scaler, ARTIFACTS / "scaler.joblib")
    with open(ARTIFACTS / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
