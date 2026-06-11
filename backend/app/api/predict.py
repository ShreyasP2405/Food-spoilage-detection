from __future__ import annotations

from fastapi import APIRouter

from app.core.config import settings
from app.core.schemas import PredictRequest, PredictionResponse
from app.ml import model as ml_model
from app.ml.traffic_light import classify

router = APIRouter()


@router.post("/predict", response_model=PredictionResponse)
async def predict(req: PredictRequest) -> PredictionResponse:
    rsl, conf, warns = ml_model.predict_single(req.model_dump())
    rsl = max(0.0, rsl)
    status, reason, factors = classify(
        rsl,
        temp_c=req.temp_c,
        humidity_pct=req.humidity_pct,
        co2_ppm=req.co2_ppm,
        methane_ppm=req.methane_ppm,
        ethylene_ppm=req.ethylene_ppm,
    )
    if warns:
        reason = reason + " (" + "; ".join(warns) + ")"
    return PredictionResponse(
        rsl_days=rsl,
        status=status,
        confidence=conf,
        model_version=settings.model_version,
        reason=reason,
        contributing_factors=factors,
    )
