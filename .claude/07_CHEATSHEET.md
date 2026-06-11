# Cheatsheet — common commands

All commands assume you're at the project root: `cd banana-storage-saver`.

## Bring up / tear down

```bash
docker-compose up --build         # first time, or after Dockerfile changes
docker-compose up -d              # subsequent runs (detached)
docker-compose ps                 # see what's running
docker-compose down               # stop + remove containers
docker-compose down -v            # also remove volumes (will lose anonymous volumes)
```

## URLs

| What | URL |
|---|---|
| Dashboard | http://localhost:5173 |
| Swagger / OpenAPI | http://localhost:8000/docs |
| Health | http://localhost:8000/api/health |
| Reference constants | http://localhost:8000/api/reference/banana |

## Logs

```bash
docker-compose logs -f                  # tail both
docker-compose logs -f backend          # backend only
docker-compose logs --tail=20 frontend  # last 20 lines of frontend
```

## Train models

```bash
# 1. Generate dataset (~1-2 min)
docker-compose exec backend python -m ml.src.dataset

# 2. RF baseline (~30 sec)
docker-compose exec backend python -m ml.src.train_rf

# 3. LSTM main model (~10 min on CPU)
docker-compose exec -d backend bash -lc \
  "python -m ml.src.train_lstm > /app/ml/artifacts/lstm_train.log 2>&1"

# Watch progress
docker-compose exec backend tail -f /app/ml/artifacts/lstm_train.log

# After training finishes, reload
docker-compose restart backend

# Verify
curl http://localhost:8000/api/health
docker-compose exec backend cat ml/artifacts/metadata.json
```

## Run tests

```bash
docker-compose exec -T backend bash -lc "cd /app/backend && pytest -q"
```

Expected output: `15 passed in ~12s`.

## Quick API smoke tests

```bash
# Health
curl http://localhost:8000/api/health

# Predict
curl -X POST http://localhost:8000/api/predict \
  -H "Content-Type: application/json" \
  -d '{"temp_c":22,"humidity_pct":70,"co2_ppm":1500,"ethylene_ppm":1.5,"methane_ppm":0,"hours_since_harvest":96,"ripeness_estimate":3}'

# Simulate (14-day timeline)
curl "http://localhost:8000/api/simulate?temp_c=14&humidity_pct=92&hours=336&initial_ripeness=2"

# Predict-CSV
curl -X POST -F "file=@data/processed/banana_synthetic_30days_sensors.csv" \
  http://localhost:8000/api/predict-csv | python -m json.tool | head -50
```

## Edit backend code (no bind-mount, requires copy + restart)

```bash
# After editing backend/app/*.py:
docker cp backend/app/main.py bss-backend:/app/backend/app/main.py
docker-compose restart backend
sleep 6
curl http://localhost:8000/api/health
```

For multiple files, use a loop or:
```bash
docker-compose up --build -d backend   # rebuild image (slower but cleaner)
```

## Edit frontend code (bind-mounted, hot reload)

Just save the file. Vite HMR picks it up. If you edited `vite.config.ts`:

```bash
docker-compose restart frontend
```

## Regenerate Excel-friendly CSV

```bash
docker cp ml/src/export_excel.py bss-backend:/app/ml/src/export_excel.py
docker-compose exec backend python -m ml.src.export_excel
docker cp bss-backend:/app/data/processed/banana_synthetic_30days_sensors.csv \
          data/processed/banana_synthetic_30days_sensors.csv
```

## Get a shell inside a container

```bash
docker-compose exec backend bash
docker-compose exec frontend sh
```

## Inspect models

```bash
# Metrics summary
docker-compose exec backend cat ml/artifacts/metadata.json

# RF model info
docker-compose exec backend python -c "import joblib; m=joblib.load('/app/ml/artifacts/rf_baseline.joblib'); print(m)"

# LSTM summary
docker-compose exec backend python -c "import tensorflow as tf; m=tf.keras.models.load_model('/app/ml/artifacts/lstm_model.keras'); m.summary()"
```

## Reset everything

```bash
# Nuke containers, images, networks, volumes
docker-compose down -v
docker rmi bss-backend:0.1.0 bss-frontend:0.1.0

# Wipe trained artifacts (will fall back to physics estimator)
rm -rf ml/artifacts/*.keras ml/artifacts/*.joblib ml/artifacts/metadata.json

# Wipe generated dataset
rm -f data/processed/banana_synthetic_v1.csv

# Rebuild from scratch
docker-compose up --build
```

## Resume on a new machine

1. Clone / copy the whole `banana-storage-saver/` folder.
2. `cd banana-storage-saver`
3. `docker-compose up --build`
4. Wait ~15 min for the backend image to build (TensorFlow is heavy).
5. Open http://localhost:5173.
6. If `ml/artifacts/` is empty, follow the *Train models* section above.

## Resume in a new AI chat

1. Open `.claude/00_RESUME_PROMPT.md`.
2. Copy entire contents.
3. Paste to a new chat with Claude / GPT / Gemini / Cursor.
4. Continue from where you left off.
