# Decision Log

Every architectural and tech-stack choice made in this project, and the reasoning. **Do not silently overturn these.**

## Scope decisions

| Decision | Why |
|---|---|
| Banana-only MVP, not multi-commodity | "Start narrow, design for extension" — the master prompt §12 specifies a 4-step extension recipe. |
| Software-only, hardware deferred | User asked for software part first. The `data_source/mqtt_stub.py` placeholder is the one file that needs implementing when ESP32 ships. |
| Synthetic physics-driven training data, no real fruit data | No public banana-spoilage time-series dataset matches the (temp, RH, gas) → (days_to_spoilage) signature. Calibrated physics from peer-reviewed sources is the honest substitute. README says so. |
| No web scraping in v1 | The user originally mentioned scraping, but the master prompt's §1 already cited the constants from peer-reviewed sources, so scraping was redundant and was explicitly skipped. |
| No auth, no multi-tenancy, no cloud | Master prompt §10 forbids these for the MVP. |

## Architecture decisions

| Decision | Why |
|---|---|
| 4-layer architecture: simulator → dataset → ML → app | Each layer depends only on the one above. Lets us swap ML model without touching API; swap simulator for real sensors without retraining. |
| `data_source` abstraction (`base.py` + `simulator.py` + `mqtt_stub.py`) | Decouples sensor source from the rest of the system. ESP32 ingest later is a one-file change. |
| Traffic light is a pure rules engine, not a learned classifier | Interpretable. Easy to tune thresholds without retraining. Returns "reason" string + contributing factors so warehouse staff sees *why* it's red. |
| Model loader fallback chain: LSTM → RF → physics | API works on a fresh repo with zero artifacts. Logged warnings tell developers what loaded. |
| Pydantic v2 with min/max validation + `clamp_features` | Out-of-distribution sensor readings clamp to training range and emit warnings, rather than feeding the model garbage. |

## Tech stack decisions

| Choice | Reason rejected alternatives |
|---|---|
| **FastAPI** (not Flask) | Pydantic v2 validation, auto Swagger, async + WebSocket native. |
| **Pydantic v2** schemas | Compile-time-ish guarantees on inputs. 422s on bad data without writing validators. |
| **Structlog JSON logging** | Production-ready. Filterable in any log aggregator. |
| **React + TypeScript + Tailwind** (not Streamlit / Flask templates) | A real warehouse dashboard needs mobile + WebSocket + interactive charts. TS keeps frontend/backend schemas in sync. |
| **Vite** (not CRA) | Faster dev server, native ESM, simpler config. |
| **Recharts** (not D3 directly) | Declarative React-native charts; no UI library beyond Tailwind. |
| **lucide-react** icons | Tree-shakeable, MIT, no font dependency. |
| **No UI library** (no MUI/AntD/Chakra) | Master prompt §10 explicitly forbade. Tailwind alone is enough. |
| **TensorFlow / Keras 3** | LSTM is the main model. Keras 3 .keras format. |
| **scikit-learn RandomForest** | Honest non-temporal baseline. |
| **joblib** for sklearn artifacts, **.keras** for TF | Standard formats. |
| **Docker Compose** (not bare venv, not k8s) | User chose Docker option B in the brief. Cross-platform reproducibility, no "works on my machine." |
| **Python 3.11** in container | TensorFlow 2.16+ supports 3.11. The user's host Python is 3.10 but irrelevant — everything is in Docker. |

## ML decisions

| Decision | Why |
|---|---|
| Two models (RF + LSTM), report both | Honest comparison. If RF matches LSTM, complexity isn't worth it. |
| LSTM window = 48 timesteps × 7 features (= 24 hours at 30-min sampling) | Per master prompt §4.1. Captures climacteric trajectory. |
| LSTM architecture fixed: LSTM(64,seq) → Dropout(0.2) → LSTM(32) → Dense(16,relu) → Dense(1) | Per master prompt §4.1 — do not change without a new spec. |
| Huber loss | Robust to outliers; better than MSE for this skewed RSL distribution. |
| Adam(1e-3), early stopping patience 5 on val_loss | Standard. |
| Split by `batch_id` (not row-level random) | Critical: random row splits leak readings from the same batch into train+test → fake high score. Per master prompt §4.2. |
| 70/15/15 train/val/test | Standard. |
| Single StandardScaler fit on training only | Per master prompt §4.4. |
| `metadata.json` includes data SHA256 | Traceability — any model can be linked to the exact CSV it was trained on. |

## Frontend mode decisions

| Mode | Why it exists |
|---|---|
| **Manual input** | Single-shot lookup. "I measured these conditions, what's the RSL?" |
| **Live simulation (WebSocket)** | Watch the model react frame-by-frame. Compelling demo. |
| **Fast-forward (slider)** | See the entire 30-day curve and exactly when it crosses thresholds. Comparison tool. |
| **Upload CSV** (added later) | Bulk-predict on real-world or other-source data. Returns annotated CSV download. |

## Things explicitly skipped

- Scraping (redundant given cited constants)
- Authentication / users
- Multi-tenancy
- Cloud deploy / k8s
- ESP32 firmware
- Real-sensor validation
- Per-batch DB / persistence — predictions are stateless. No history table.
- Email/SMS/webhook alerts
- Multi-commodity (rice/wheat/mango)
- GPU TensorFlow build (CPU is sufficient for this model size; user has RTX 4050 but model only takes ~10 min on CPU)

## Decisions that may be revisited

| Topic | Current state | When to revisit |
|---|---|---|
| `on_time_warning_rate` is 0.0 | Dataset over-weights `red` rows (70%). | When generating v2 dataset, stop simulating each batch shortly after first spoilage. See `05_KNOWN_ISSUES.md`. |
| Single-sample LSTM prediction repeats the row 48 times | Degraded but functional fallback for `/api/predict`. | When real time-series data exists, prefer `/api/predict-sequence`. |
| MQ-sensor ADC formula is linear | Real MQ sensors use `log10(Rs/R0) → log10(ppm)`. | When real ESP32 firmware lands, use proper datasheet curve in firmware (not in simulator). |
