# Banana Storage Saver — Intelligent Food Storage MVP

Predicts the **Remaining Shelf Life (RSL)** in days for stored Cavendish bananas from temperature, humidity, and gas readings, using a physics-grounded simulator and a learned LSTM model. The dashboard surfaces a traffic-light status, a countdown, and the contributing factors so a warehouse operator can act *before* spoilage starts.

## Honest scope

- **Banana-only.** Architected for multi-commodity extension (see `docs/EXTENDING.md`); not implemented yet.
- **Simulated data.** The model is trained on synthetic readings produced by a physics simulator calibrated to published Cavendish post-harvest constants (UC Davis, Goldfinger study). Real-sensor validation is explicit future work.
- **No hardware in this MVP.** ESP32 + DHT22 + MQ-4 + MQ-135 ingest is stubbed behind a `DataSource` interface so it can drop in later without touching the model or UI.

## Architecture

See `docs/ARCHITECTURE.md`. Short version:

```
[ Frontend (Vite/React/TS/Tailwind) ] ── HTTP/WS ──▶ [ FastAPI ] ── loads ──▶ [ ml/artifacts ]
                                                          │
                                                          └─ uses ─▶ ml/src/simulator.py
                                                                     (also drives /api/simulate
                                                                      and /ws/stream)
```

Three frontend modes:
1. **Manual input** — sliders → `/api/predict` → traffic light + countdown.
2. **Live simulation** — WebSocket stream of physics-driven readings + live predictions.
3. **Fast-forward** — runs the simulator forward with constant conditions and animates the resulting timeline so the user sees *when* it goes yellow → red.

## Quickstart (Docker)

```bash
docker-compose up --build
# then open:
#   http://localhost:5173   (dashboard)
#   http://localhost:8000/docs  (Swagger)
```

The first time you start, `ml/artifacts/` is empty — the backend falls back to a physics-based RSL estimate so the UI still works. To get an actual ML model, train one (below).

## Train a model

Inside the backend container (or a local Python 3.11 venv with `pip install -r backend/requirements.txt`):

```bash
# 1. Generate the synthetic dataset
python -m ml.src.dataset

# 2. Train the random-forest baseline
python -m ml.src.train_rf

# 3. (Optional) train the LSTM main model — needs TensorFlow
python -m ml.src.train_lstm
```

Artifacts land in `ml/artifacts/`. Restart the backend (Docker volume already mounts the directory) and `/api/health` will report `model_kind: rf` (or `lstm`).

The notebooks under `ml/notebooks/` (`01_generate_dataset` → `04_lstm_training`) reproduce the same pipeline interactively.

## The science

Calibration constants and modelling laws used:

- **Arrhenius** for temperature-dependent respiration (`Ea ≈ 80,000 J/mol`, `Q10 ≈ 2.5`).
- **Climacteric curve** with peak ~5.5× base rate at ripeness stage 5, matching the published 56.8 mg CO₂/kg/h figure.
- **Michaelis-Menten / first-order kinetics** for container gas accumulation with realistic leak rate.
- **Anaerobic methane** triggers only after late-stage tissue collapse — the system's irreversible spoilage signal.

Full citations and equations: `docs/SCIENCE.md`.

## ML metrics

Metrics are written to `ml/artifacts/metadata.json` after training. Fields:

| Metric | Meaning |
|---|---|
| `mae_days`, `rmse_days`, `r2` | Standard regression metrics on held-out batches (split by `batch_id`, not row, to prevent leakage). |
| `on_time_warning_rate_24h` | Of batches that actually spoil, fraction we flagged red ≥ 24 h before. Target ≥ 0.90. |
| `false_alarm_rate` | Green-status rows wrongly predicted as ≤ 2 days RSL. |

## Tests

```bash
cd backend && pytest
```

Covers simulator determinism, the temperature → shelf-life monotonicity, traffic-light rules, the predict happy path, validation errors, and the simulate endpoint.

## Roadmap

- Multi-commodity support (rice, wheat, mango, tomato) per `docs/EXTENDING.md`.
- Real ESP32 + DHT22 + MQ-4 + MQ-135 ingest via the existing `data_source/` interface (only `mqtt_stub.py` needs implementing).
- Field validation against ground-truth spoilage logs.
- Per-batch history database and alert webhooks.

## Citations

- UC Davis Postharvest Technology Center — *Banana recommendations for maintaining postharvest quality*.
- Chitarra & Chitarra — *Pós-Colheita de Frutas e Hortaliças* (banana ripeness scale).
- Goldfinger banana respiration study (ResearchGate).
- Banana 1-MCP shelf-life study at 27 °C (Academia.edu).
