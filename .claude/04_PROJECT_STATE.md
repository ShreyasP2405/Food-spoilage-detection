# Current Project State

Snapshot of what's running, what's verified, and what's next.

## Live services

| Service | Port | URL | Status |
|---|---|---|---|
| Backend | 8000 | http://localhost:8000 | up, LSTM loaded |
| Swagger | 8000 | http://localhost:8000/docs | up |
| Frontend | 5173 | http://localhost:5173 | up, 4 tabs working |

Both containers run via `docker-compose up`.

## Verified endpoints

| Endpoint | Method | Verified |
|---|---|---|
| `/api/health` | GET | ✅ returns `{model_loaded: true, model_kind: "lstm", model_version: "0.1.0"}` |
| `/api/predict` | POST | ✅ 22°C/70% RH/ripeness 3 → 1.2 days, RED |
| `/api/predict-sequence` | POST | ✅ |
| `/api/simulate` | GET | ✅ 14°C/92% RH 14-day timeline matches UC Davis |
| `/api/predict-csv` | POST | ✅ 49-row CSV → 49 predictions with status counts and annotated download |
| `/ws/stream` | WS | ✅ live frames every 1s |
| `/api/reference/banana` | GET | ✅ |

## ML artifacts

Located in `ml/artifacts/` (mounted into backend container):

| File | Size | Purpose |
|---|---|---|
| `lstm_model.keras` | ~410 KB | Main model |
| `rf_baseline.joblib` | ~120 MB | Random Forest baseline |
| `scaler.joblib` | ~700 B | StandardScaler fit on training data |
| `metadata.json` | ~1.5 KB | Metrics, training date, data SHA256, feature order |
| `lstm_train.log` | ~10 KB | Training log from last LSTM run |

## Final metrics (from metadata.json)

| Metric | RF baseline | LSTM (main) |
|---|---|---|
| Test MAE (days) | 0.022 | **0.024** |
| Test RMSE (days) | 0.077 | **0.043** |
| Test R² | 0.9992 | **0.9997** |
| On-time warning rate (24h) | 0.0 ⚠ | 0.0 ⚠ |
| False alarm rate | 0.0 | 0.0 |

⚠ See `05_KNOWN_ISSUES.md` for why on-time-warning is 0.0 — it's a dataset-shape issue, not a model bug.

## Tests

- 15 tests in `backend/tests/`, all passing
- Run: `docker-compose exec backend pytest -q`
- Coverage: simulator determinism + Arrhenius monotonicity + spoils-at-room-temp, traffic-light rules, predict happy path, predict 422 validation, simulate timeline, reference, clamp_features

## Datasets generated

| File | Rows | Notes |
|---|---|---|
| `data/processed/banana_synthetic_v1.csv` | 105,449 | Full training set; gitignored |
| `data/processed/banana_synthetic_30days_sensors.csv` | 12,686 | Sensor-named columns for Excel; 45 batches |

## Frontend tabs (all functional)

1. **Manual input** — sliders → POST /api/predict → traffic light + countdown + reason
2. **Live simulation** — WS /ws/stream → real-time chart fill, 1 sec = 30 sim min
3. **Fast-forward** — GET /api/simulate → scrubbable timeline
4. **Upload CSV** — drag-drop CSV → POST /api/predict-csv → status counts, RSL stats, sensor chart, per-row table, download annotated CSV

## What runs the next time you `docker-compose up`

If you `down` and `up` again:
- Backend will load the existing LSTM artifact (already trained)
- Frontend will hot-reload from mounted `src/`
- No re-training needed

If artifacts are deleted:
- Backend falls back to physics estimator (`_physics_fallback_rsl`)
- API still works; UI still works; just less accurate predictions
- Re-train: `docker-compose exec backend python -m ml.src.dataset && docker-compose exec backend python -m ml.src.train_rf && docker-compose exec backend python -m ml.src.train_lstm && docker-compose restart backend`

## Next likely tasks (in priority order)

1. Fix dataset balance so on_time_warning_rate becomes meaningful (stop simulating each batch shortly after first spoilage). Easy edit in `ml/src/simulator.py:stream` or `ml/src/dataset.py`.
2. Add real banana data ingestion (when collected). Replace `data_source/mqtt_stub.py` with an aiomqtt client.
3. Add a 2nd commodity per `docs/EXTENDING.md`. 4-step recipe.
4. Add per-batch persistence (Postgres or even SQLite) for history charts.
5. Add alerts (webhook on red transition).
