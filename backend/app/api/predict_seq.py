from __future__ import annotations

from fastapi import APIRouter

from app.core.config import settings
from app.core.schemas import PredictSequenceRequest, PredictionResponse
from app.ml import model as ml_model
from app.ml.traffic_light import classify

router = APIRouter()


@router.post("/predict-sequence", response_model=PredictionResponse)
async def predict_sequence(req: PredictSequenceRequest) -> PredictionResponse:
    rows = [r.model_dump() for r in req.readings]
    rsl, conf, warns = ml_model.predict_sequence(rows)
    rsl = max(0.0, rsl)
    last = req.readings[-1]
    status, reason, factors = classify(
        rsl,
        temp_c=last.temp_c,
        humidity_pct=last.humidity_pct,
        co2_ppm=last.co2_ppm,
        methane_ppm=last.methane_ppm,
        ethylene_ppm=last.ethylene_ppm,
    )
    if warns:
        reason = reason + " (" + "; ".join(warns[:3]) + ")"
    return PredictionResponse(
        rsl_days=rsl,
        status=status,
        confidence=conf,
        model_version=settings.model_version,
        reason=reason,
        contributing_factors=factors,
    )
