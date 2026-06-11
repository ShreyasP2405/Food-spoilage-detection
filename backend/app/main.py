from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Make the repo root importable so `from ml.src.simulator import ...` works
# whether we run inside Docker or as `uvicorn app.main:app` from backend/.
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import settings  # noqa: E402
from app.api.predict import router as predict_router  # noqa: E402
from app.api.predict_seq import router as predict_seq_router  # noqa: E402
from app.api.predict_csv import router as predict_csv_router  # noqa: E402
from app.api.simulate import router as simulate_router  # noqa: E402
from app.api.stream import router as stream_router  # noqa: E402
from app.api.health import router as health_router  # noqa: E402
from app.ml import model as ml_model  # noqa: E402


def _configure_logging() -> None:
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level, logging.INFO),
    )
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    _configure_logging()
    log = structlog.get_logger()
    bundle = ml_model.load_model()
    log.info("startup", model_kind=bundle.kind, model_version=settings.model_version)
    yield
    log.info("shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.model_version,
        description="Predicts Remaining Shelf Life (RSL) for stored bananas from temperature, humidity and gas readings.",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(predict_router, prefix="/api", tags=["predict"])
    app.include_router(predict_seq_router, prefix="/api", tags=["predict"])
    app.include_router(predict_csv_router, prefix="/api", tags=["predict"])
    app.include_router(simulate_router, prefix="/api", tags=["simulate"])
    app.include_router(health_router, prefix="/api", tags=["meta"])
    app.include_router(stream_router, tags=["stream"])
    return app


app = create_app()
