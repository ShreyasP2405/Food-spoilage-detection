from __future__ import annotations

import asyncio
import json
import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.config import settings
from app.data_source.simulator import SimulatedDataSource
from app.ml import model as ml_model
from app.ml.traffic_light import classify

router = APIRouter()
log = logging.getLogger(__name__)


@router.websocket("/ws/stream")
async def ws_stream(
    websocket: WebSocket,
    temp_c: float = Query(22.0),
    humidity_pct: float = Query(70.0),
    initial_ripeness: float = Query(2.0),
    tick_seconds: float = Query(1.0, ge=0.1, le=10.0),
):
    await websocket.accept()
    src = SimulatedDataSource(
        temp_c=temp_c,
        humidity_pct=humidity_pct,
        initial_ripeness=initial_ripeness,
        tick_seconds=tick_seconds,
    )
    try:
        async for reading in src.stream():
            features = {
                "temp_c": reading["temp_c"],
                "humidity_pct": reading["humidity_pct"],
                "co2_ppm": reading["co2_ppm"],
                "ethylene_ppm": reading["ethylene_ppm"],
                "methane_ppm": reading["methane_ppm"],
                "hours_since_harvest": reading["hours_since_harvest"],
                "ripeness_estimate": reading["ripeness_estimate"],
            }
            rsl, conf, _ = ml_model.predict_single(features)
            rsl = max(0.0, rsl)
            status, reason, factors = classify(
                rsl,
                temp_c=reading["temp_c"],
                humidity_pct=reading["humidity_pct"],
                co2_ppm=reading["co2_ppm"],
                methane_ppm=reading["methane_ppm"],
                ethylene_ppm=reading["ethylene_ppm"],
            )
            payload = {
                "reading": reading,
                "prediction": {
                    "rsl_days": rsl,
                    "status": status,
                    "reason": reason,
                    "confidence": conf,
                    "model_version": settings.model_version,
                    "contributing_factors": [f.model_dump() for f in factors],
                },
            }
            await websocket.send_text(json.dumps(payload))
    except WebSocketDisconnect:
        log.info("client disconnected from /ws/stream")
    except asyncio.CancelledError:
        pass
    finally:
        await src.close()
