from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter

from app.core.config import settings
from app.core.schemas import HealthResponse, ReferenceResponse
from app.ml import model as ml_model

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    bundle = ml_model.get_bundle()
    return HealthResponse(
        status="ok",
        model_loaded=bundle.kind != "none",
        model_kind=bundle.kind,
        model_version=settings.model_version,
    )


@router.get("/reference/banana", response_model=ReferenceResponse)
async def banana_reference() -> ReferenceResponse:
    path = Path(settings.references_dir) / "banana_postharvest_constants.json"
    with open(path, "r", encoding="utf-8") as f:
        return ReferenceResponse(constants=json.load(f))
