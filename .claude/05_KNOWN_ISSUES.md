# Known Issues & Caveats

These are *known*. **Do not silently "fix" them** — most need a conversation first because they involve scope tradeoffs.

## 1. on_time_warning_rate is 0.0

**Symptom.** In `ml/artifacts/metadata.json` the test metric `on_time_warning_rate_24h: 0.0` and `false_alarm_rate: 0.0`.

**Why it's not a model bug.** The metric is defined as: *"of batches that ended up spoiling, fraction where the model first predicted RSL ≤ 2 days at least 24 h before actual spoilage"*. With our current dataset, ~70% of rows are already labeled `red` because most batches at hot/dry regimes spoil within 1–2 days of harvest. By the time the dataset captures them, the 24-hour-warning window has already passed.

**Root cause.** `ml/src/simulator.py:stream` keeps simulating up to 30 days even after `is_spoiled` becomes true (it stops only when ripeness > 7.5). This produces many redundant red rows.

**Fix (when you do this).** Either:
- (a) Stop emitting rows shortly after `is_spoiled` first becomes true (e.g., 12 hours later). Easy edit.
- (b) Cap dataset rows per batch.
- (c) Compute the warning-rate metric differently (e.g., transitions only, not row-level).

**Why we haven't fixed it.** The MAE / R² are excellent; the warning-rate is a *secondary* metric and the project status is "MVP complete, real-sensor validation is next phase." The README is honest about this. But this is the #1 thing to fix before any "production" claim.

## 2. Single-sample LSTM uses repeated-row window

**Symptom.** When you call `POST /api/predict` (one reading), the LSTM expects 48 timesteps. We currently fill the window by repeating the same row 48 times. The response includes a warning: *"Single-sample LSTM call uses repeated-row window; prefer /predict-sequence."*

**Why this is fine for now.** The frontend's Manual Input mode is designed for "what does this snapshot mean", not for time-series inference. The LSTM degrades to roughly RF performance in this mode because it has no actual temporal information. CSV upload also uses single-row windows per row, which is the same compromise.

**Proper fix.** Use `POST /api/predict-sequence` whenever you have actual history. The CSV upload endpoint could be upgraded to use a sliding 48-window per row instead of single-row repeats — would meaningfully improve accuracy on uploaded time-series.

## 3. MQ-sensor ADC formula is linear

**Symptom.** In `ml/src/simulator.py`, `gas_mq135_raw` and `gas_mq4_raw` are computed with linear formulas:
```python
mq135 = clamp(80 + 0.04 * co2_obs + 5.0 * eth_obs + noise, 0, 1023)
mq4 = clamp(60 + 60.0 * ch4_obs + 0.005 * co2_obs + noise, 0, 1023)
```

**Why this is wrong (in real life).** Real MQ sensors are heated metal-oxide and follow a power-law `Rs/R0 → ppm` curve. We used linear because (a) the model learns the mapping anyway, (b) it's only emitted as supplementary features.

**Proper fix.** When real ESP32 firmware lands, the *firmware* should convert ADC → ppm using the datasheet formulas. The simulator should match. For now, neither matters because the model trains directly on ppm.

## 4. RF baseline is enormous (~120 MB)

**Symptom.** `rf_baseline.joblib` is 120 MB. Way bigger than the LSTM's 410 KB.

**Why.** RandomForestRegressor with `n_estimators=200, max_depth=20` on 105k rows produces big trees.

**Why we keep it.** It's the honest baseline. Reducing trees would make the comparison less honest.

**If size matters.** Drop to `n_estimators=50, max_depth=15` — still gives a meaningful baseline at 1/4 the size.

## 5. TensorFlow on CPU only

**Symptom.** TF logs show `Could not find cuda drivers on your machine, GPU will not be used.` The user has an RTX 4050 but it's unused.

**Why.** TensorFlow ≥ 2.11 dropped native Windows GPU support. The container would need NVIDIA Container Toolkit + a CUDA-aware TF base image (e.g., `nvcr.io/nvidia/tensorflow:24.03-tf2-py3`) which is ~10 GB.

**Decision.** Not worth it. LSTM trains in ~10 min on CPU. GPU setup time > training time.

## 6. Frontend volume mounts are partial

**Symptom.** Initially edits to `frontend/vite.config.ts` weren't picked up by the running container.

**Why.** `docker-compose.yml` only mounted `frontend/src` and `frontend/index.html`. Other config files (`vite.config.ts`, `tsconfig.json`, `tailwind.config.ts`, `postcss.config.js`) had to be added manually.

**Status.** Fixed in current `docker-compose.yml`.

## 7. Backend doesn't auto-reload on code changes

**Symptom.** Editing files in `backend/app/` and saving doesn't restart the FastAPI process inside the container.

**Why.** The backend container has `backend/`, `ml/`, `data/` baked in via `COPY` in the Dockerfile. They're not bind-mounted.

**Workaround.** After editing backend code, copy the files in and restart:
```bash
docker cp backend/app/main.py bss-backend:/app/backend/app/main.py
docker-compose restart backend
```

Or rebuild: `docker-compose up --build -d backend`.

**Proper fix (if you want).** Add bind-mounts to `docker-compose.yml`:
```yaml
backend:
  volumes:
    - ./backend:/app/backend
    - ./ml:/app/ml
    - ./data:/app/data
  command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir /app/backend --reload
```
Not done because the project is currently stable; rebuilds are infrequent.

## 8. RF artifact is loaded into memory even when LSTM is preferred

**Symptom.** `ml/model.py:load_model` falls through LSTM → RF → physics. If LSTM loads, RF is never loaded into memory. Good.

But: the file `rf_baseline.joblib` is still copied into the container image (~120 MB) on build. Image size is 5+ GB regardless.

**Decision.** Acceptable. Single-image deployment is simpler than splitting model artifacts into a separate image.

## 9. No history / no DB

The system is fully stateless. Predictions aren't logged. Time-series history shown in the dashboard's Live mode is in-memory only and lost on refresh.

**Decision.** Per master prompt §10: "Do not add user authentication, multi-tenancy, or cloud deployment in this MVP." Persistence falls in that category. v0.2 idea: SQLite or Postgres for batch history.

## 10. Docker images are large

| Image | Size |
|---|---|
| bss-backend | ~5.5 GB (TensorFlow is heavy) |
| bss-frontend | ~600 MB |

**Decision.** Acceptable for dev. For production, multi-stage build for backend (separate `tf-base` and `app` stages) would shave ~2 GB. Not done because the project is dev-only right now.
