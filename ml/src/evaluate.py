"""
Standalone evaluation: loads saved artifacts and reports test metrics.
Usage:
  python -m ml.src.evaluate --model rf
  python -m ml.src.evaluate --model lstm
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from .train_rf import (
    DATA_PATH,
    ARTIFACTS,
    FEATURES,
    TARGET,
    split_by_batch,
    on_time_warning_rate,
    false_alarm_rate,
)
from .train_lstm import WINDOW, make_windows


def evaluate_rf() -> dict:
    model = joblib.load(ARTIFACTS / "rf_baseline.joblib")
    scaler = joblib.load(ARTIFACTS / "scaler.joblib")
    df = pd.read_csv(DATA_PATH)
    _, _, test_df = split_by_batch(df)
    X = scaler.transform(test_df[FEATURES].values)
    y = test_df[TARGET].values
    yp = model.predict(X)
    return {
        "mae_days": float(mean_absolute_error(y, yp)),
        "rmse_days": float(np.sqrt(mean_squared_error(y, yp))),
        "r2": float(r2_score(y, yp)),
        "on_time_warning_rate_24h": float(on_time_warning_rate(test_df, yp)),
        "false_alarm_rate": float(false_alarm_rate(test_df, yp)),
    }


def evaluate_lstm() -> dict:
    import tensorflow as tf
    model = tf.keras.models.load_model(ARTIFACTS / "lstm_model.keras")
    scaler = joblib.load(ARTIFACTS / "scaler.joblib")
    df = pd.read_csv(DATA_PATH)
    _, _, test_df = split_by_batch(df)
    X, y, anchor = make_windows(test_df, scaler)
    yp = model.predict(X, batch_size=512).flatten()
    return {
        "mae_days": float(mean_absolute_error(y, yp)),
        "rmse_days": float(np.sqrt(mean_squared_error(y, yp))),
        "r2": float(r2_score(y, yp)),
        "on_time_warning_rate_24h": float(on_time_warning_rate(anchor, yp)),
        "false_alarm_rate": float(false_alarm_rate(anchor, yp)),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=["rf", "lstm"], default="rf")
    args = parser.parse_args()
    metrics = evaluate_rf() if args.model == "rf" else evaluate_lstm()
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
