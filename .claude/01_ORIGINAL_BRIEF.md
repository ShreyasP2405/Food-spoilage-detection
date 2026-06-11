# Original Brief

## The user's original ask

The user described an "Intelligent Grain/Food Storage Saver" — an IoT + ML system that predicts spoilage before it happens, for agriculture / warehousing.

Hardware (out of scope for MVP):
- DHT11/DHT22 (Temp/Humidity)
- MQ-4 (Methane)
- MQ-135 (CO2/NH3/ethylene cross-sensitive)
- ESP32 microcontroller
- MQTT transport

ML claim:
- Food releases specific gases as it begins to rot before it smells bad to humans.
- ML analyzes correlation between temperature, humidity, and gas levels to predict "Days until Spoilage."

Uniqueness:
- Reduces food waste.
- Most agriculture projects focus on growing (irrigation); this focuses on storage.

User's chosen scope for v1:
- **Software-only**
- **One commodity (banana)** — start narrow, design for multi-commodity later
- **Frontend website + Python backend with FastAPI + ML model**
- Use Kaggle or seed data; user explicitly mentioned synthetic seed data + web scraping in the original brief
- "use venv" for ML — later overridden to "use Docker"

## Master Prompt v1 (what actually built the project)

The user pasted a fully-formed master prompt that locked in every architectural choice. It is reproduced verbatim below as the source of truth. If something contradicts it, the master prompt wins.

Key constraints from the master prompt:
- Project layout in `§2` is exact, must match
- Scientific grounding constants in `§1` must NOT be improvised
- LSTM architecture in `§4.1` is fixed: `Input(48,7) → LSTM(64, return_sequences=True) → Dropout(0.2) → LSTM(32) → Dense(16, relu) → Dense(1, linear)`, Huber loss, Adam(1e-3), early stopping
- Split by `batch_id` 70/15/15 to prevent leakage
- LSTM is the main model, RF is honest baseline
- Three frontend modes: Manual / Live / Fast-forward
- Tailwind only, no heavyweight UI library
- Docker compose brings up the whole stack
- README must say: "Trained on physics-simulated data calibrated to published Cavendish banana respiration parameters (Arrhenius + Michaelis-Menten); validation against held-out simulated curves and qualitative match to UC Davis shelf-life tables. Real-sensor validation is future work."

## Master Prompt v1 — Verbatim

```
# MASTER PROMPT — Intelligent Food Storage Saver (Banana MVP)

## 0. ROLE & MISSION

You are a senior full-stack ML engineer. Build the software-only MVP of an
Intelligent Food Storage Saver — a system that predicts the Remaining Shelf
Life (RSL) in days for bananas (Cavendish, Musa acuminata AAA) stored under
varying environmental conditions, using simulated IoT sensor data.

This is the banana-only MVP. The architecture must be designed so that adding
new commodities (rice, wheat, mango, tomato) later is a config change, not a
rewrite.

Hardware (ESP32 + DHT22 + MQ-4 + MQ-135) is NOT in scope right now. The
backend must expose a clean `data_source` abstraction so that real
MQTT-streamed sensor data can replace the simulator later by swapping one
module.

## 1. SCIENTIFIC GROUNDING (DO NOT IMPROVISE THESE NUMBERS)

(Calibration table: optimal storage 13–14°C, optimal RH 90–95%,
shelf life @ 14°C in air 2–4 weeks, shelf life @ 27°C 7d untreated / 11d w/ 1-MCP,
climacteric peak CO2 56.8 mg/kg/h untreated, up to 74.2 with ethylene,
ripe banana CO2 7.6 L/kg/h vs 1.2 L/kg/h cold, ripe ethylene up to 7.4 µL C2H4/kg/h,
chilling injury < 13°C, CO2 toxicity > 7%.)

Modeling laws: Arrhenius temperature dependence, Q10 ≈ 2-3,
Michaelis-Menten kinetics, climacteric curve.

## 2. PROJECT STRUCTURE

(Exact tree specified — `backend/`, `ml/`, `data/`, `frontend/`, `docs/` with
specific subfolders and file names.)

## 3. THE PHYSICS-BASED BANANA SIMULATOR (CORE OF THE PROJECT)

Builds `ml/src/simulator.py`. State variables, sensor outputs, equations,
container gas accumulation, spoilage definition, dataset generation
(>=50,000 pairs, 1000 batches, varied conditions, 30-min sampling).

## 4. ML MODEL

Random Forest baseline + LSTM main model. Split by batch_id 70/15/15.
Metrics in metadata.json: MAE, RMSE, R2, on-time warning rate (>= 90% target),
false alarm rate.

## 5. BACKEND API (FastAPI)

Endpoints: POST /api/predict, POST /api/predict-sequence,
GET /api/simulate, WS /ws/stream, GET /api/health, GET /api/reference/banana.

CORS to localhost:5173. Pydantic v2. Structlog JSON. /docs Swagger.

## 6. FRONTEND

Three modes: Manual / Live (WebSocket) / Fast-forward (timeline scrub).
Dark mode default. Big RSL number. Animated traffic light. Mobile responsive.
Tailwind only.

## 7. SIMULATION DATA STREAM CONTRACT

SensorReading schema with timestamp, batch_id, temp_c, humidity_pct,
co2_ppm, ethylene_ppm, methane_ppm, gas_mq135_raw, gas_mq4_raw,
hours_since_harvest, ripeness_estimate.

## 8. DEFENSIVE ENGINEERING

Pydantic min/max, clamp+warn, "calibrating..." placeholder, deterministic
simulator with seed, Dockerfile per service, docker-compose up.

## 9. README REQUIREMENTS

Elevator pitch, honest scope, screenshot, architecture diagram, quickstart,
science section, metrics table, roadmap, citations.

## 10. WHAT NOT TO DO

No invented respiration numbers, no overclaim, no hardcoded MQTT in main path,
no MUI/AntDesign, no row-level random splits, no large CSVs committed, no auth.

## 11. DELIVERABLES CHECKLIST

docker-compose up works, /docs Swagger UI, /5173 dashboard, pytest passes,
notebook runs end-to-end, README complete with screenshots, SCIENCE.md cites
>=3 papers.

## 12. EXTENSION HOOK

Add new commodity = (1) JSON constants file, (2) simulator subclass,
(3) retrain, (4) frontend selector. If more is needed, architecture is wrong.
```

## After-the-fact additions during the session

Decisions that were NOT in the master prompt but were made during the session:

- User chose **Docker (B)** + **full breadth (B)** when asked.
- LSTM was trained successfully (~25 epochs, early stopped). Final test MAE 0.024 days, R² 0.9997.
- Added a 4th frontend tab: **Upload CSV** with download-annotated-CSV. (Section "A strict + flexible alias map".)
- Added `docs/PROFESSOR_GUIDE.md` (a beginner-friendly walkthrough document).
- Added `data/processed/banana_synthetic_30days_sensors.csv` — Excel-friendly export with sensor-named columns.
- pytest, httpx, pytest-asyncio added to backend Dockerfile (so dev deps bake into the image).

The current state matches all of the above. See `04_PROJECT_STATE.md`.
