# Banana Storage Saver — Complete Software Walkthrough

A beginner-friendly, end-to-end guide to every part of the project. Written so you can read it once, skim it before the meeting, and keep it open as a reference during the demo.

---

## 1. The problem we're solving

Every year ~14% of food produced globally is lost between harvest and retail (FAO). Bananas are especially vulnerable: they spoil fast, climacterically (a sharp ripening burst), and warehouses today rely on visual inspection — which catches problems *after* they're irreversible.

**Our claim:** by monitoring temperature, humidity, and the gases bananas release as they respire, software can predict *days until spoilage* — giving warehouses 24–48 hours of warning to ventilate, cool, or sell early.

This MVP delivers the **software half** end-to-end. The hardware (ESP32 with DHT22, MQ-135, MQ-4 sensors) is intentionally out of scope right now — we built the architecture so it can plug in later by replacing exactly one file.

---

## 2. The four pieces, and how they fit

```
┌────────────────────────────────────────────────────────────┐
│  Layer 1 — Physics simulator                               │
│  ml/src/simulator.py                                       │
│  Models how bananas actually rot, calibrated to UC Davis   │
│  postharvest research                                      │
└──────────────┬─────────────────────────────────────────────┘
               │
               ▼
┌────────────────────────────────────────────────────────────┐
│  Layer 2 — Synthetic dataset                               │
│  ml/src/dataset.py  →  banana_synthetic_v1.csv             │
│  Runs the simulator across 432 banana batches and labels   │
│  every reading with "days until spoilage"                  │
└──────────────┬─────────────────────────────────────────────┘
               │
               ▼
┌────────────────────────────────────────────────────────────┐
│  Layer 3 — Machine learning models                         │
│  ml/src/train_rf.py  → Random Forest baseline              │
│  ml/src/train_lstm.py → LSTM main model                    │
│  Saved as joblib + Keras files                             │
└──────────────┬─────────────────────────────────────────────┘
               │
               ▼
┌────────────────────────────────────────────────────────────┐
│  Layer 4 — Application                                     │
│  Backend: FastAPI loads model, exposes REST + WebSocket    │
│  Frontend: React dashboard with 3 modes                    │
│  Both run as Docker containers                             │
└────────────────────────────────────────────────────────────┘
```

The **rule** that keeps the project clean: *each layer only depends on the one above it*. We can swap the ML model without touching the API, swap the API without touching the UI, swap the simulator for real sensors without retraining.

---

## 3. Layer 1 — The physics simulator

**File:** `ml/src/simulator.py`

This is the most important piece. It encodes how a real banana actually decays, using equations from peer-reviewed agricultural science.

### What it models

| Phenomenon | Equation we use | Source |
|---|---|---|
| Temperature → respiration rate | **Arrhenius**: `k(T) = exp(-Eₐ/R · (1/T − 1/T_ref))` with Eₐ=80 kJ/mol | Standard biochemistry |
| Climacteric ripening burst | Piecewise multiplier peaking at stage 5, calibrated to **56.8 mg CO₂/kg/h** | Goldfinger banana study |
| Ethylene production | Peaks at **7.4 µL/kg/h** at climacteric | Banana aerobic respiration literature |
| Humidity stress | Linear stress factor `1 + 0.02·|RH − 92.5|` | UC Davis (optimal 90–95%) |
| Container gas balance | `dC/dt = production − k_leak · C` | First-order leak ODE |
| Methane onset | Triggers only at ripeness > 7.2 (anaerobic) | Food microbiology |
| Chilling injury | Below 13°C tissue damage starts | UC Davis |

### What "days until spoilage" means

For any state (temp, humidity, current ripeness), the simulator runs forward with conditions held constant and counts how long until any of three irreversible things happens:
1. Ripeness stage ≥ 7
2. Cumulative environmental stress crosses threshold
3. Methane appears (anaerobic decomposition started)

That's our **regression target** — a ground-truth label we can use to train ML.

### Why a simulator instead of real data?

There is no public banana-spoilage dataset matching the (temp, humidity, CO₂, ethylene, methane) → (days-to-spoilage) signature we need. Collecting real data takes weeks per batch. **Calibrated physics is the honest substitute** until real sensors come online.

> **Talking point for your professor:** *"We built a digital twin of a banana grounded in three peer-reviewed papers. The simulator alone validates against published shelf-life tables — 14°C/92% RH gives us 14 days of life, matching UC Davis. Then we use the simulator to generate ML training data."*

---

## 4. Layer 2 — Generating the dataset

**File:** `ml/src/dataset.py`
**Output:** `data/processed/banana_synthetic_v1.csv` (105,449 rows)

We sweep across realistic warehouse conditions:

| Dimension | Values |
|---|---|
| Temperature | 5°C (cold), 14°C (optimal), 22°C (room), 32°C (hot), dynamic day-night sin curves |
| Humidity | 50%, 70%, 92% |
| Initial ripeness | Stages 1.2, 2.0, 3.0 |
| Container leak rate | Normal (0.15/h), poorly ventilated (0.05/h) |
| Random seeds | 4 batches per combo |

= **432 batches × ~250 readings each = 105k rows.**

Each row contains the 12 sensor outputs plus the ground-truth `days_until_spoilage` and a `green/yellow/red` traffic-light status.

We also exported **`banana_synthetic_30days_sensors.csv`** (~12.7k rows, 45 batches) with explicit sensor-named columns (`DHT22_temperature_C`, `MQ135_co2_ppm`, `MQ4_methane_ppm`, etc.) for examiner-friendly inspection in Excel.

> **Talking point:** *"This isn't 'fake' data — it's physics-driven synthetic data. Every row obeys Arrhenius kinetics and climacteric ripening curves. The CSV your professor can open in Excel shows the climacteric CO₂ peak around day 4–5 at room temperature, matching textbook biology."*

---

## 5. Layer 3 — The ML models

We train **two** models for an honest comparison:

### Random Forest baseline (`ml/src/train_rf.py`)
- **Input:** flat features — 7 sensor values from one moment in time
- **Output:** predicted days_until_spoilage
- **Why:** an honest non-temporal baseline. If a model that ignores time history can predict well, the LSTM has to beat it to be worth the complexity.

### LSTM main model (`ml/src/train_lstm.py`)
- **Input:** sliding window of the **last 48 readings** (= 24 hours at 30-min sampling) × 7 features
- **Architecture:**
  ```
  Input(48, 7)
   → LSTM(64, return_sequences=True)
   → Dropout(0.2)
   → LSTM(32)
   → Dense(16, ReLU)
   → Dense(1, linear)         # predicts days_until_spoilage
  ```
- **Loss:** Huber (robust to outliers)
- **Optimizer:** Adam with learning rate 1e-3
- **Stopping:** Early stopping on validation loss (patience 5 epochs)
- **Why LSTM:** spoilage is a *time-series* problem. The same temperature now means different things depending on whether it's been hot for an hour or a week. LSTMs are specifically designed for this.

### Critical detail: split by *batch*, not by row

If we randomly split rows, readings from the same banana could appear in train *and* test → trivial leak → false high score. We split by `batch_id` so test bananas are *unseen entirely*.

70 / 15 / 15 train / val / test.

### Results we got

| Metric | RF baseline | LSTM |
|---|---|---|
| MAE (test, days) | 0.022 | **0.024** |
| RMSE (test, days) | 0.077 | **0.043** |
| R² (test) | 0.9992 | **0.9997** |

The LSTM has *lower RMSE and higher R²* — it benefits from seeing the time history, even though MAE is similar. Both models clearly learned the physics.

> **Talking point — and an honest caveat:** *"R² of 0.9997 means we successfully learned the simulator. It does NOT mean we can deploy this in a real warehouse tomorrow. Real-sensor validation is explicit future work — and we say so in the README. Anyone who deploys this without collecting real fruit data is misusing it."*

---

## 6. Layer 4 — The application

### 6a. Backend — FastAPI (Python)

**Folder:** `backend/app/`

A web service that loads the trained LSTM at startup and exposes endpoints. Key files:

| File | Job |
|---|---|
| `main.py` | App entry, CORS, model loading on startup |
| `core/schemas.py` | Pydantic v2 input/output validation |
| `core/config.py` | Environment variables |
| `ml/model.py` | Model loader: tries LSTM → Random Forest → physics fallback |
| `ml/preprocess.py` | Clamps inputs outside training distribution |
| `ml/traffic_light.py` | Pure rules: RSL + raw conditions → `green/yellow/red` + reason |
| `data_source/base.py` | Abstract sensor interface |
| `data_source/simulator.py` | Wraps the physics simulator for live preview |
| `data_source/mqtt_stub.py` | Placeholder for future ESP32 ingest |

### Endpoints

| Method | Path | What it does |
|---|---|---|
| POST | `/api/predict` | One sensor reading → RSL + status + reason |
| POST | `/api/predict-sequence` | Window of readings → RSL using full LSTM context |
| GET | `/api/simulate` | Run physics forward N days → return full timeline |
| WebSocket | `/ws/stream` | Live readings + predictions every 1 sec |
| GET | `/api/health` | Model loaded? Which kind? |
| GET | `/api/reference/banana` | Returns the postharvest constants JSON |

### Traffic-light rules (`traffic_light.py`)

Not a learned classifier — a **transparent rules engine** so a warehouse manager can see *why* something is red:

```
RED:    RSL ≤ 2 days  OR  methane > 0.5 ppm  OR  any critical factor
YELLOW: RSL ≤ 5 days  OR  temp > 25°C  OR  RH < 80%
GREEN:  otherwise
```

It also returns *contributing factors* with severity — so the dashboard shows "Temperature 27°C exceeds typical storage; respiration accelerated" rather than just a red light.

> **Talking point:** *"We deliberately separated the prediction from the alert logic. The ML predicts a number; rules turn it into action. This is more interpretable, easier to debug, and easier to change without retraining."*

### 6b. Frontend — React + TypeScript + Tailwind

**Folder:** `frontend/src/`

Single-page dashboard with three tabs, each calling a different endpoint:

#### Mode 1 — Manual input
Sliders for every sensor + ripeness stage. Click *Predict*. Calls `POST /api/predict`. Shows the traffic light, the RSL countdown ("4.2 days remaining"), the reason, and a list of contributing factors.

**Use case:** "I just measured these conditions. How bad is it?"

#### Mode 2 — Live simulation
Pick conditions → click *Start* → opens `WS /ws/stream`. Server pushes a fresh reading + prediction every 1 real second (= 30 simulated minutes). Chart fills in real time. Traffic light updates frame by frame. You can literally watch a banana spoil at warehouse-time-compressed.

**Use case:** demonstration to non-technical people; gut-check the model's behavior.

#### Mode 3 — Fast-forward
Pick conditions → set horizon (up to 30 days) → calls `GET /api/simulate` once → backend returns the entire 30-day timeline → drag a slider to scrub through it.

**Use case:** "If I keep these conditions, when does it cross from green to red?"

### Visual design choices
- Dark mode default — calm aesthetic, not gamified
- Big readable RSL number ("4.2 days remaining") at center stage
- Animated soft-pulse on the active traffic light
- Tooltips on every sensor explaining the science ("Ethylene rises during the climacteric phase…")
- `recharts` for plots, `lucide-react` for icons, no heavyweight UI library

---

## 7. How everything runs together — Docker

**File:** `docker-compose.yml`

Two services:

```
backend:  Python 3.11, FastAPI on :8000  (mounts ml/artifacts/ for hot-reload of models)
frontend: Node 20, Vite dev server on :5173  (proxies /api and /ws → backend)
```

Why Docker: the professor (or anyone) can run the whole stack with one command on any OS. No "it works on my machine."

### One command to run everything
```bash
cd banana-storage-saver
docker-compose up --build
```

Then open:
- **http://localhost:5173** — dashboard
- **http://localhost:8000/docs** — auto-generated Swagger API docs

### One command to retrain
```bash
docker-compose exec backend python -m ml.src.dataset      # build dataset
docker-compose exec backend python -m ml.src.train_rf     # baseline
docker-compose exec backend python -m ml.src.train_lstm   # main model
docker-compose restart backend                             # reload artifact
```

---

## 8. Project structure cheat-sheet

```
banana-storage-saver/
├── README.md                   ← elevator pitch + quickstart
├── docker-compose.yml          ← one-command bring-up
├── .env / .env.example         ← config knobs
│
├── backend/                    ← FastAPI app
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py
│   │   ├── api/                ← predict, predict_seq, simulate, stream, health
│   │   ├── core/               ← config, schemas
│   │   ├── ml/                 ← model loader, preprocess, traffic_light
│   │   └── data_source/        ← simulator + mqtt_stub
│   └── tests/                  ← pytest (15 tests, all pass)
│
├── ml/                         ← data + model training
│   ├── notebooks/              ← 4 notebooks: generate, EDA, RF, LSTM
│   ├── src/                    ← simulator, dataset, train_rf, train_lstm, evaluate
│   └── artifacts/              ← lstm_model.keras, rf_baseline.joblib, scaler.joblib, metadata.json
│
├── data/
│   ├── processed/              ← banana_synthetic_v1.csv (full), 30days_sensors.csv (Excel)
│   └── references/             ← banana_postharvest_constants.json (cited)
│
├── frontend/                   ← React + Vite + TS + Tailwind
│   ├── Dockerfile
│   ├── src/
│   │   ├── api/client.ts
│   │   ├── components/         ← TrafficLight, RSLCountdown, SensorChart, panels
│   │   ├── hooks/              ← useWebSocket, usePrediction
│   │   └── pages/Dashboard.tsx
│   └── vite.config.ts
│
└── docs/
    ├── SCIENCE.md              ← citations + equations
    ├── ARCHITECTURE.md         ← diagram + data flow
    ├── API.md                  ← endpoint contracts
    ├── EXTENDING.md            ← how to add rice/wheat/mango
    └── PROFESSOR_GUIDE.md      ← this document
```

---

## 9. Demo script for your professor (10 min)

**Minute 0–1: Open the README.** One paragraph elevator pitch. Show the *honest scope* statement — banana-only MVP, simulated data, hardware deferred. (This earns trust immediately.)

**Minute 1–3: Open `data/processed/banana_synthetic_30days_sensors.csv` in Excel.** Show:
- The sensor-named columns (DHT22, MQ-135, MQ-4) — clearly mapped to real hardware
- Filter to one batch (e.g., `room_22C__moderate_70pct__breaker_stage2`)
- Make a quick line chart of `MQ135_co2_ppm` over time → show the **climacteric peak** around day 4–5. *"This is the actual biological signature of a ripening banana."*

**Minute 3–4: Open `ml/src/simulator.py`.** Point to the Arrhenius equation and the climacteric multiplier. Cite the constants table in `data/references/banana_postharvest_constants.json` with sources.

**Minute 4–5: Open `ml/artifacts/metadata.json`.** Show the metrics table — both models, MAE in *days*, R². *"The split is by batch_id, not by row, to prevent leakage."*

**Minute 5–8: Run `docker-compose up`.** Open http://localhost:5173.
- **Manual mode:** slide temp to 22°C, RH to 65%, hours to 96 → click Predict → "1.2 days, RED, ethylene rising sharply"
- **Live mode:** Start. Watch CO₂ rise on the chart. Watch traffic light flip yellow then red. *"This is one real second per 30 simulated minutes. The browser is talking to FastAPI over a WebSocket."*
- **Fast-forward mode:** set 14°C / 92% RH → run → drag slider → *"At optimal storage we predict ~14 days. Now drag to 22°C — only 7 days. This matches UC Davis postharvest tables exactly."*

**Minute 8–9: Open Swagger at http://localhost:8000/docs.** Show the auto-generated API documentation. Show the response schema for `/api/predict` — RSL + status + reason + contributing factors.

**Minute 9–10: Open `docs/EXTENDING.md`.** Walk through the 4-step recipe for adding a new commodity (rice, mango). *"This is why we built it as a banana-only MVP — the architecture extends without rewriting."*

**Closing line:** *"The MVP is software-complete. Hardware integration is one file change in `data_source/mqtt_stub.py`. Real-sensor validation is the next phase. We've kept every claim honest — no overpromising."*

---

## 10. Likely professor questions, and how to answer

**Q: How do you know the simulator is right?**
A: Three checks. (1) The constants come from peer-reviewed papers cited in `docs/SCIENCE.md`. (2) Predicted shelf life at 14°C/92% RH is ~14 days, matching UC Davis postharvest tables. (3) The CO₂ curve shows the climacteric peak in the right place (around stage 5, ~day 4–5 at room temperature). It's a *digital twin*, not a black box.

**Q: Why two models?**
A: The Random Forest is an honest non-temporal baseline. If it predicts as well as the LSTM, we don't need the LSTM. In our case the LSTM has lower RMSE (0.043 vs 0.077) — the time history matters. We report both metrics so a reviewer can judge.

**Q: What's the on-time-warning rate?**
A: Currently 0.0 — and we say so honestly in the metadata. **Not a model bug.** It's a dataset-shape issue: 70% of rows are already labeled `red` because most batches at hot/dry regimes spoil within 1–2 days, so the metric (which checks *first* red prediction ≥ 24h before actual spoilage) has almost no qualifying batches. Fix in v0.2: stop simulating each batch shortly after first spoilage.

**Q: Why FastAPI, not Flask?**
A: Three reasons. (1) Pydantic v2 input validation is automatic and rigorous — out-of-range CO₂ values are rejected before they reach the model. (2) Auto-generates OpenAPI/Swagger docs at `/docs`. (3) Async + WebSocket support out of the box, which we need for the live mode.

**Q: Why React + TypeScript and not Streamlit/Flask templates?**
A: A real warehouse dashboard needs to be responsive on mobile (warehouse staff), needs WebSocket for live updates, and needs interactive charts. TypeScript gives compile-time guarantees that the frontend and backend agree on the data schema.

**Q: What happens if no model is trained yet?**
A: The backend gracefully falls back to the physics-based RSL estimator (`_physics_fallback_rsl` in `ml/model.py`). API still works, UI still works. We logged a warning so a developer notices.

**Q: How do you handle inputs outside training range?**
A: `ml/preprocess.py` clamps every feature to its observed training range and emits warnings. Real-world sensors do drift — this prevents the model from extrapolating wildly. Confidence is also returned as part of the prediction.

**Q: What about the hardware?**
A: Three sensors specified — DHT22 (temp + humidity), MQ-135 (CO₂ + ethylene cross-sensitive), MQ-4 (methane). The simulator emits *both* the physical quantities (ppm) and the raw 0-1023 ADC counts the ESP32 would actually see. When real hardware comes online, we replace `data_source/mqtt_stub.py` — that's the only file change needed. We deliberately did NOT couple ESP32 logic into the rest of the codebase.

**Q: Test coverage?**
A: 15 unit + integration tests, all passing. Covers simulator determinism (with seed), Arrhenius monotonicity, predict happy path, predict validation errors, simulate timeline, traffic-light rules, the reference endpoint. Run: `docker-compose exec backend pytest`.

**Q: What's the next step?**
A: 20 real bananas, 4 weeks, 3 storage conditions. Even 100 hours of real data dramatically improves a synthetic-pretrained model. Then we ship the ESP32 firmware and `mqtt_stub.py` becomes `mqtt.py`.

---

## 11. The two slides if you only have time for two

**Slide 1 — Problem & approach**
- 14% of food lost between harvest and retail
- Existing solutions are reactive (visual inspection)
- Our claim: temp + humidity + gas → predict spoilage 24-48h early
- Banana MVP, software-only, hardware-ready architecture

**Slide 2 — What we built**
- Physics simulator calibrated to UC Davis (Arrhenius + climacteric)
- 105k synthetic readings → LSTM (MAE 0.024 days, R² 0.9997)
- FastAPI backend + React dashboard, all dockerized
- Honest scope: simulated data — real-sensor validation is next phase

---

## 12. Sensor stack reference

| Sensor | Measures | Range | Why included |
|---|---|---|---|
| **DHT22** | Temperature + humidity | -40 to +80°C, 0-100% RH | Single most important predictor — drives Arrhenius respiration rate |
| **MQ-135** | CO₂, NH₃, ethylene cross-sensitive | 10-1000 ppm typical | Catches climacteric CO₂ rise + ammonia from late protein breakdown |
| **MQ-4** | Methane (CH₄) | 200-10,000 ppm | Late-stage anaerobic decomposition — irreversible spoilage signal |

The simulator emits both physical units (ppm) **and** raw ADC counts (0–1023) the ESP32 would see, so the same model can be retrained against either representation.

---

## 13. Data dictionary (for the Excel CSV)

| Column | Type | Meaning |
|---|---|---|
| `batch_id` | str | Unique simulated batch identifier |
| `regime_temperature` | str | Temperature regime label (cold_5C, optimal_14C, room_22C, hot_32C, dayNight_22pm5) |
| `regime_humidity` | str | Humidity regime (dry_50pct, moderate_70pct, optimal_92pct) |
| `regime_initial_ripeness` | str | Starting ripeness (green_stage1, breaker_stage2, yellowing_stage3) |
| `timestamp_utc` | str | Synthetic timestamp (epoch 2026-04-01 UTC) |
| `elapsed_hours` | float | Hours since harvest |
| `elapsed_days` | float | Same in days |
| `DHT22_temperature_C` | float | DHT22 temperature reading, °C, ±0.3 noise |
| `DHT22_humidity_percent` | float | DHT22 RH reading, %, ±2 noise |
| `MQ135_co2_ppm` | float | CO₂ headspace concentration, ppm |
| `MQ135_ethylene_ppm` | float | Ethylene headspace concentration, ppm |
| `MQ4_methane_ppm` | float | Methane headspace concentration, ppm |
| `MQ135_raw_adc_0to1023` | int | What the ESP32 ADC would read from MQ-135 |
| `MQ4_raw_adc_0to1023` | int | What the ESP32 ADC would read from MQ-4 |
| `ripeness_stage_1to7` | int | Chitarra & Chitarra peel-color scale (1=green, 7=overripe) |
| `predicted_days_until_spoilage` | float | Ground-truth label, forward-projected |
| `traffic_light_status` | str | green / yellow / red |

---

## 14. Glossary (terms a beginner might trip on)

- **Climacteric:** the burst of respiration and ethylene production that drives ripening in some fruits (banana, mango, tomato). Non-climacteric fruits (citrus, grapes) don't have this burst.
- **Arrhenius equation:** the relationship that says reaction rates rise exponentially with temperature. Used everywhere in chemistry and biology.
- **Q10:** the factor by which a biological rate increases per 10°C rise. For fruit respiration, ~2-3.
- **Postharvest:** the period after harvest, before consumption — storage, transport, retail.
- **RSL (Remaining Shelf Life):** our model's prediction in days.
- **Climacteric peak:** the moment of maximum CO₂/ethylene production, ~day 4-5 at room temperature for bananas.
- **LSTM (Long Short-Term Memory):** a neural network architecture designed for time-series data; remembers context across many timesteps.
- **Random Forest:** an ensemble of decision trees; the standard tabular ML baseline.
- **Sliding window:** taking the last N timesteps as input to predict the next value.
- **Pydantic:** Python library for runtime data validation; we use it to reject invalid API inputs before they reach the model.
- **WebSocket:** a persistent two-way connection between browser and server, unlike single-shot HTTP. We use it for live streaming.
- **Docker container:** a packaged application with its own filesystem and dependencies. Runs identically on any machine.

---

This is everything. Read it once for understanding, skim it again before the meeting, keep it open as a reference during the demo. If your professor pushes on any specific part, you have the file path + line of reasoning to point to.
