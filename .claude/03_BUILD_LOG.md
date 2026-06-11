# Build Log — chronological

What was built in what order, with the file paths.

## Phase 1 — Scaffolding & physics layer

1. Created project tree per master prompt §2 (`backend/`, `ml/`, `data/`, `frontend/`, `docs/`)
2. `data/references/banana_postharvest_constants.json` — calibration constants from UC Davis + Goldfinger study
3. `ml/src/simulator.py` — physics-grounded BananaSimulator with Arrhenius, climacteric, container gas balance, methane onset
4. `ml/src/dataset.py` — sweep generator across 6 temp regimes × 3 RH × 3 ripeness × 2 leak rates × 4 seeds = 432 batches
5. `ml/src/train_rf.py` — Random Forest baseline with batch-level split, on-time-warning + false-alarm metrics
6. `ml/src/train_lstm.py` — LSTM(64,seq) → Dropout → LSTM(32) → Dense(16) → Dense(1), Huber, Adam(1e-3), early stopping
7. `ml/src/evaluate.py` — standalone metric reporter
8. Notebooks: `01_generate_dataset`, `02_eda`, `03_baseline_random_forest`, `04_lstm_training`

## Phase 2 — Backend

9. `backend/pyproject.toml` + `requirements.txt`
10. `backend/app/core/config.py` (pydantic-settings, BSS_* env vars)
11. `backend/app/core/schemas.py` (SensorReading, PredictRequest, PredictionResponse, etc.)
12. `backend/app/ml/preprocess.py` (FEATURE_ORDER, clamp_features)
13. `backend/app/ml/traffic_light.py` (rules engine returning status + reason + factors)
14. `backend/app/ml/model.py` (loader: LSTM → RF → physics fallback)
15. `backend/app/data_source/base.py` + `simulator.py` + `mqtt_stub.py`
16. `backend/app/api/predict.py` — POST /api/predict
17. `backend/app/api/predict_seq.py` — POST /api/predict-sequence
18. `backend/app/api/simulate.py` — GET /api/simulate
19. `backend/app/api/stream.py` — WS /ws/stream
20. `backend/app/api/health.py` — GET /api/health, GET /api/reference/banana
21. `backend/app/main.py` — FastAPI app, CORS, lifespan model loading, structlog JSON
22. `backend/tests/conftest.py` + `test_simulator.py` + `test_model.py` + `test_api.py` (15 tests)

## Phase 3 — Frontend

23. `frontend/package.json`, `vite.config.ts`, `tsconfig.json`, `tailwind.config.ts`, `postcss.config.js`, `index.html`
24. `frontend/src/main.tsx`, `App.tsx`, `index.css`
25. `frontend/src/api/client.ts` — typed fetch wrappers
26. `frontend/src/hooks/usePrediction.ts`, `useWebSocket.ts`
27. `frontend/src/components/TrafficLight.tsx`, `RSLCountdown.tsx`, `SensorChart.tsx`, `EnvironmentControls.tsx`
28. `frontend/src/components/ManualInputPanel.tsx`, `SimulationPanel.tsx`, `TimeSlider.tsx`
29. `frontend/src/pages/Dashboard.tsx`

## Phase 4 — Infra & docs

30. `backend/Dockerfile` (Python 3.11 slim) — later patched to bake in pytest, httpx, pytest-asyncio
31. `frontend/Dockerfile` (Node 20 alpine)
32. `docker-compose.yml` with both services, volume mounts for `ml/artifacts/`, `data/`, frontend `src/`
33. `docs/SCIENCE.md`, `ARCHITECTURE.md`, `API.md`, `EXTENDING.md`
34. `README.md`, `.gitignore`, `.env.example`

## Phase 5 — First runs & debugging

35. `docker-compose up --build` — both containers came up clean
36. `docker-compose exec backend python -m ml.src.dataset` → 105,449 rows
37. `docker-compose exec backend python -m ml.src.train_rf` → R² 0.999
38. LSTM training first attempt — user Ctrl-C'd at epoch 1
39. Re-launched LSTM training in background, polled with watcher script
40. LSTM finished after 25 epochs (early stopped) → val MAE 0.022 days, test MAE 0.024, R² 0.9997
41. Restarted backend → `/api/health` returned `model_kind: lstm`

## Phase 6 — Bug fix: dashboard "model: offline"

42. Browser DevTools showed `/api/health` failing
43. Root cause: `vite.config.ts` proxy hardcoded `localhost:8000`, but inside frontend container `localhost` ≠ backend container
44. Compounding: Docker image had old `vite.config.ts` baked in; `frontend/src` was mounted but `vite.config.ts` was not
45. Fix:
    - Switched proxy target to `process.env.VITE_API_BASE` (defaults to `http://backend:8000` from compose, falls back to `http://localhost:8000` outside Docker)
    - Added `vite.config.ts`, `tsconfig.json`, `tailwind.config.ts`, `postcss.config.js` to docker-compose volume mounts
    - Recreated frontend container

## Phase 7 — Polish & extras

46. Added `.env` (with same defaults as `.env.example`) so docker-compose `env_file` flows through
47. Patched `docker-compose.yml` services with `env_file: { path: .env, required: false }`
48. Created `ml/src/export_excel.py` to produce `data/processed/banana_synthetic_30days_sensors.csv` with sensor-named columns (DHT22_*, MQ135_*, MQ4_*) for examiner-friendly inspection
49. Wrote `docs/PROFESSOR_GUIDE.md` — beginner-friendly walkthrough with demo script, likely Q&A, glossary, sensor stack table, full data dictionary

## Phase 8 — CSV upload feature

50. `backend/app/api/predict_csv.py` — POST /api/predict-csv (multipart upload, batch LSTM prediction, alias map for sensor-named columns, returns annotated CSV + per-row JSON + summary stats)
51. Added `python-multipart` to `requirements.txt`
52. Wired router into `backend/app/main.py`
53. Added `postPredictCsv()` to `frontend/src/api/client.ts`
54. `frontend/src/components/CsvUploadPanel.tsx` — drag-drop upload, status count cards, RSL stats, sensor chart, per-row table with click-to-inspect, traffic light + RSL countdown for selected row, download annotated CSV
55. Added 4th tab "Upload CSV" to `frontend/src/pages/Dashboard.tsx`
56. Verified end-to-end: 49-row CSV → 49 predictions, correctly flags `4.76°C` as chilling-injury

## Phase 9 — Session capture (current)

57. `.claude/` folder created with all the session-context docs you're reading now
