# Architecture

```
                                                       ┌────────────────────┐
                                                       │   Frontend (Vite)  │
                                                       │   React + TS + TW  │
                                                       │  Dashboard 3 modes │
                                                       └──────────┬─────────┘
                                                                  │ HTTP / WS
                                                                  ▼
┌──────────────────────┐    ┌───────────────────────────────────────────────────┐
│ ml/src (importable)  │    │                  Backend (FastAPI)                │
│  simulator.py        │◄───┤                                                   │
│  dataset.py          │    │  /api/predict, /api/predict-sequence,             │
│  train_rf.py         │    │  /api/simulate, /api/health, /api/reference/...   │
│  train_lstm.py       │    │  /ws/stream                                       │
│  evaluate.py         │    │                                                   │
└──────────┬───────────┘    │   ml/model.py  ──► loads scaler + RF/LSTM         │
           │                │   ml/preprocess  ─► clamp + scale features        │
           │ joblib/keras   │   ml/traffic_light ─► RSL → status + reasons      │
           ▼                │   data_source/{simulator,mqtt_stub}.py            │
   ml/artifacts/            └───────────────────────────────────────────────────┘
   ├── lstm_model.keras                              ▲
   ├── rf_baseline.joblib                            │
   ├── scaler.joblib                                 │
   └── metadata.json                                 │
                                                     │
                                          (future)   │
                                  ┌───────────────────────────────┐
                                  │ ESP32 + DHT22 + MQ-4 + MQ-135 │
                                  │   MQTT publish via mqtt_stub  │
                                  └───────────────────────────────┘
```

## Components

**`ml/src/simulator.py`** — Single source of truth for the physics. Used both by the training pipeline (offline) and by the backend (online, for the `/api/simulate` endpoint and the WebSocket stream).

**`backend/app/data_source/`** — Abstract `DataSource` interface with a `SimulatedDataSource` (current MVP) and a placeholder `MqttDataSource` (future). The WebSocket and the live preview consume from this interface, so the rest of the system never imports the simulator directly through the data path. Swapping in real ESP32 ingest later means implementing one class.

**`backend/app/ml/model.py`** — Model loader. Tries LSTM → RF → physics fallback in that order. Held in module-level state and refreshed only by `load_model()` (called once from FastAPI's lifespan). Single-sample requests use `predict_single`; sliding-window requests use `predict_sequence`.

**`backend/app/ml/traffic_light.py`** — Pure rules engine. Takes RSL + raw conditions and returns `(status, reason, contributing_factors[])`. Independent of the model so we can change rules without retraining.

**Frontend** — Three modes share three primitives: `TrafficLight`, `RSLCountdown`, `SensorChart`. Manual mode hits `/api/predict`. Live mode opens `/ws/stream`. Fast-forward mode calls `/api/simulate` and animates the returned timeline locally.

## Data flow (live simulation)

```
slider change ──► useStream() opens WS to /ws/stream?temp_c=&humidity_pct=
                                       │
                                       ▼
              SimulatedDataSource.step() advances physics one tick
                                       │
                                       ▼
              ml.predict_single(features) → rsl_days, confidence
                                       │
                                       ▼
              traffic_light.classify(rsl, conditions) → status, reason, factors
                                       │
                                       ▼
              JSON frame → frontend appends → chart + traffic light update
```
