# Environment Details

Everything an AI assistant needs to know about *where this is running*.

## User's machine

| Property | Value |
|---|---|
| OS | Windows 11 Home Single Language (10.0.26200) |
| Shell | bash (in Claude Code) — Unix syntax, not cmd/PowerShell |
| Project root | `c:\Users\rachi\OneDrive\Desktop\shreyas\banana-storage-saver\` |
| Host Python | 3.10 — **not used.** Everything runs in Docker containers. |
| GPU | RTX 4050 — present but **not used** (CPU-only TensorFlow inside container) |
| Docker | Docker Desktop, WSL2 backend, working |
| Time zone | IST (UTC+5:30) |

## Containers (services)

| Container | Image | Internal port | Host port | Notes |
|---|---|---|---|---|
| `bss-backend` | `bss-backend:0.1.0` (Python 3.11 slim) | 8000 | 8000 | TensorFlow, FastAPI, model artifacts |
| `bss-frontend` | `bss-frontend:0.1.0` (Node 20 alpine) | 5173 | 5173 | Vite dev server, hot reload |

Network: default Compose bridge. Inside the network, services reach each other by service name (`backend:8000`, `frontend:5173`).

## Bind mounts (live-edit paths)

`docker-compose.yml` bind-mounts these from host → container:

| Service | Host path | Container path | Why |
|---|---|---|---|
| backend | `./ml/artifacts` | `/app/ml/artifacts` | Hot-load retrained models without rebuild |
| backend | `./data` | `/app/data` | Dataset CSVs accessible |
| frontend | `./frontend/src` | `/app/src` | React HMR |
| frontend | `./frontend/index.html` | `/app/index.html` | HMR |
| frontend | `./frontend/vite.config.ts` | `/app/vite.config.ts` | Config edits take effect on restart |
| frontend | `./frontend/tsconfig.json` | `/app/tsconfig.json` | |
| frontend | `./frontend/tailwind.config.ts` | `/app/tailwind.config.ts` | |
| frontend | `./frontend/postcss.config.js` | `/app/postcss.config.js` | |

**Backend code is NOT bind-mounted.** Editing `backend/app/*.py` requires either `docker cp` + `docker-compose restart backend`, or `docker-compose up --build`.

## Environment variables

Backend reads from `BSS_*` prefix (see `backend/app/core/config.py`):

| Var | Default | Purpose |
|---|---|---|
| `BSS_LOG_LEVEL` | `INFO` | structlog level |
| `BSS_CORS_ORIGINS` | `["http://localhost:5173","http://127.0.0.1:5173"]` | CORS allow list |
| `BSS_ARTIFACTS_DIR` | repo `ml/artifacts` | Where to load model from |
| `BSS_REFERENCES_DIR` | repo `data/references` | Where to load constants from |
| `BSS_PREFER_LSTM` | `true` | Try LSTM first, fall back to RF |
| `BSS_MODEL_VERSION` | `0.1.0` | Reported in /api/health |

Frontend reads:

| Var | Default | Purpose |
|---|---|---|
| `VITE_API_BASE` | `http://localhost:8000` (outside Docker) / `http://backend:8000` (set by compose) | Vite proxy target for `/api` and `/ws` |

`.env` and `.env.example` files exist at project root with the BSS_* defaults. `docker-compose.yml` services use `env_file: { path: .env, required: false }` so it's optional.

## Common paths inside the backend container

```
/app/
├── backend/
│   └── app/        ← FastAPI app source
├── ml/
│   ├── src/        ← simulator, dataset, train_*, evaluate
│   └── artifacts/  ← models, scaler, metadata.json (bind-mounted)
└── data/
    ├── processed/  ← banana_synthetic_*.csv
    └── references/ ← banana_postharvest_constants.json
```

`PYTHONPATH=/app:/app/backend` so `from ml.src.simulator import ...` and `from app.core.schemas import ...` both work.

## Common paths inside the frontend container

```
/app/
├── src/                    ← bind-mounted (HMR)
├── index.html              ← bind-mounted (HMR)
├── vite.config.ts          ← bind-mounted (restart needed)
├── tsconfig.json           ← bind-mounted
├── tailwind.config.ts      ← bind-mounted
├── postcss.config.js       ← bind-mounted
├── package.json            ← baked in image
└── node_modules/           ← baked in image
```

## Trained model state

| Artifact | Value |
|---|---|
| Model kind currently loaded | LSTM |
| Trained on | `banana_synthetic_v1.csv` (105,449 rows) |
| Training data SHA256 | `2b0e4c0ca0a5871e0d453dfd0f6ec95b3598e0adcee9d469abb52b2e8dccfac1` (in metadata.json) |
| Training duration | ~9 minutes (CPU, 25 epochs, early stopped) |
| Model file size | ~410 KB |
