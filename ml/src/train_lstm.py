"""
LSTM trainer.

Sliding window of last 48 readings (24h at 30-min sampling) of 7 features
predicts days_until_spoilage at the *last* timestep.

Architecture:
  Input(48, 7)
  -> LSTM(64, return_sequences=True)
  -> Dropout(0.2)
  -> LSTM(32)
  -> Dense(16, relu)
  -> Dense(1, linear)

Loss: Huber. Optimizer: Adam(1e-3). Early stopping on val loss.
Split is by batch_id 70/15/15.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from .train_rf import (
    DATA_PATH,
    ARTIFACTS,
    FEATURES,
    TARGET,
    file_sha,
    split_by_batch,
    on_time_warning_rate,
    false_alarm_rate,
)

WINDOW = 48


def make_windows(df: pd.DataFrame, scaler) -> tuple[np.ndarray, np.ndarray, pd.DataFrame]:
    """Return X (n,48,7), y (n,), and the row-anchor df (for per-batch metrics).
    The 'anchor' row is the last row of each window (i.e. prediction target row)."""
    Xs, ys, anchors = [], [], []
    for batch_id, g in df.groupby("batch_id"):
        g = g.sort_values("timestamp_h").reset_index(drop=True)
        if len(g) < WINDOW:
            continue
        feats = scaler.transform(g[FEATURES].values)
        target = g[TARGET].values
        for i in range(WINDOW - 1, len(g)):
            Xs.append(feats[i - WINDOW + 1 : i + 1])
            ys.append(target[i])
            anchors.append(g.iloc[i])
    if not Xs:
        return np.empty((0, WINDOW, len(FEATURES))), np.empty((0,)), pd.DataFrame()
    return np.asarray(Xs, dtype=np.float32), np.asarray(ys, dtype=np.float32), pd.DataFrame(anchors).reset_index(drop=True)


def main():
    import tensorflow as tf
    from tensorflow.keras import layers, Model
    from tensorflow.keras.callbacks import EarlyStopping
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(DATA_PATH)
    train_df, val_df, test_df = split_by_batch(df)

    scaler = StandardScaler().fit(train_df[FEATURES].values)

    X_train, y_train, _ = make_windows(train_df, scaler)
    X_val, y_val, _ = make_windows(val_df, scaler)
    X_test, y_test, anchor_test = make_windows(test_df, scaler)

    inp = layers.Input(shape=(WINDOW, len(FEATURES)))
    x = layers.LSTM(64, return_sequences=True)(inp)
    x = layers.Dropout(0.2)(x)
    x = layers.LSTM(32)(x)
    x = layers.Dense(16, activation="relu")(x)
    out = layers.Dense(1, activation="linear")(x)
    model = Model(inp, out)
    model.compile(optimizer=tf.keras.optimizers.Adam(1e-3), loss=tf.keras.losses.Huber(), metrics=["mae"])

    es = EarlyStopping(patience=5, restore_best_weights=True, monitor="val_loss")
    model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=40,
        batch_size=256,
        callbacks=[es],
        verbose=2,
    )

    y_pred_val = model.predict(X_val, batch_size=512).flatten()
    y_pred_test = model.predict(X_test, batch_size=512).flatten()

    metrics = {
        "model": "lstm",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "data_sha256": file_sha(DATA_PATH),
        "feature_order": FEATURES,
        "target": TARGET,
        "window": WINDOW,
        "val": {
            "mae_days": float(mean_absolute_error(y_val, y_pred_val)),
            "rmse_days": float(np.sqrt(mean_squared_error(y_val, y_pred_val))),
            "r2": float(r2_score(y_val, y_pred_val)),
        },
        "test": {
            "mae_days": float(mean_absolute_error(y_test, y_pred_test)),
            "rmse_days": float(np.sqrt(mean_squared_error(y_test, y_pred_test))),
            "r2": float(r2_score(y_test, y_pred_test)),
            "on_time_warning_rate_24h": float(on_time_warning_rate(anchor_test, y_pred_test)),
            "false_alarm_rate": float(false_alarm_rate(anchor_test, y_pred_test)),
        },
    }

    model.save(ARTIFACTS / "lstm_model.keras")
    joblib.dump(scaler, ARTIFACTS / "scaler.joblib")

    md_path = ARTIFACTS / "metadata.json"
    if md_path.exists():
        with open(md_path, "r", encoding="utf-8") as f:
            existing = json.load(f)
        if isinstance(existing, list):
            existing.append(metrics)
        else:
            existing = [existing, metrics]
        with open(md_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)
    else:
        with open(md_path, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)

    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
