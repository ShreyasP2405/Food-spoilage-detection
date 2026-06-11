# Extending to New Commodities

This MVP is banana-only by design. The architecture is set up so adding a new commodity (rice, mango, tomato, wheat, …) is a four-step recipe — no rewrite required.

## 1. Add a constants file

Create `data/references/{commodity}_constants.json` modelled on `banana_postharvest_constants.json`. At minimum:

- `optimal.{temp_c_target, humidity_pct_target}`
- `danger_thresholds` — chilling, toxicity, etc.
- `respiration` — base rate at reference temp, peak rate, ethylene peak (or 0 for non-climacteric)
- `kinetics.activation_energy_J_per_mol`, reference temp, Q10
- `climacteric: true | false`

Source the numbers from peer-reviewed postharvest data and cite them in `docs/SCIENCE.md`.

## 2. Subclass the simulator

Create `ml/src/simulator_{commodity}.py` that subclasses `BananaSimulator` (which we'll rename to `BaseSimulator` once the second commodity lands). For climacteric fruits override `_climacteric_multiplier` and `_ethylene_curve`. For non-climacteric (e.g., grapes, citrus, rice) override those to return constants and put the spoilage logic on humidity/microbial growth instead of ripeness.

## 3. Re-train

Two options:

- **Per-commodity model** — easiest. Re-run `dataset.py` with the new simulator, then `train_rf.py` and `train_lstm.py`. Save artifacts under `ml/artifacts/{commodity}/`.
- **Shared backbone, commodity-specific heads** — more accurate as you scale to many commodities. Add a one-hot commodity feature, train one shared LSTM, then optionally fine-tune the last Dense layer per commodity.

Update `metadata.json` so the backend can pick the right artifact set per commodity.

## 4. Wire the frontend

Add a commodity picker to the dashboard header. The picker drives:

- Which `/api/reference/{commodity}` payload is fetched (for slider ranges and tooltips).
- Which model bundle the backend uses (`?commodity=rice` query param, or a route prefix).

If your architecture forces more than these four steps, something has been over-coupled — fix it before adding the next commodity.

## Notes on hardware

Different commodities benefit from different sensors:

- **Climacteric fruits** (banana, mango, tomato): MQ-135 (CO₂/NH₃) + ethylene-specific sensor (e.g., MQ-309A or a dedicated electrochemical cell).
- **Grains** (rice, wheat): DHT22 humidity is the dominant signal; CO₂ from microbial respiration; methane (MQ-4) for late-stage spoilage.
- **Leafy greens**: ethylene less important; focus on humidity, temperature, and ammonia (MQ-135).

The `data_source/mqtt_stub.py` payload schema is commodity-agnostic — only the calibration curve from raw ADC to ppm changes, and that lives in firmware.
