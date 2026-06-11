from __future__ import annotations

from fastapi import APIRouter, Query

from app.core.config import settings
from app.core.schemas import SimulateResponse, SimulateTimelinePoint
from app.ml.traffic_light import classify
from ml.src.simulator import BananaSimulator, DEFAULT_DT_HOURS

router = APIRouter()


@router.get("/simulate", response_model=SimulateResponse)
async def simulate(
    temp_c: float = Query(22.0, ge=-10, le=50),
    humidity_pct: float = Query(70.0, ge=20, le=100),
    hours: int = Query(168, ge=1, le=24 * 30),
    initial_ripeness: float = Query(2.0, ge=1.0, le=6.0),
    sample_every_h: float = Query(3.0, ge=0.5, le=12.0),
) -> SimulateResponse:
    """Run the simulator forward with constant conditions and return the timeline.
    Used by the frontend's Time Fast-Forward mode."""
    sim = BananaSimulator(initial_ripeness=initial_ripeness, seed=0)
    timeline: list[SimulateTimelinePoint] = []
    sample_steps = max(1, int(sample_every_h / DEFAULT_DT_HOURS))
    n_steps = int(hours / DEFAULT_DT_HOURS)
    for i in range(n_steps):
        sim.step(dt_h=DEFAULT_DT_HOURS, temp_c=temp_c, rh_pct=humidity_pct)
        if i % sample_steps == 0:
            r = sim.read_sensor(with_noise=False)
            status, _, _ = classify(
                r.days_until_spoilage,
                temp_c=r.temp_c,
                humidity_pct=r.humidity_pct,
                co2_ppm=r.co2_ppm,
                methane_ppm=r.methane_ppm,
                ethylene_ppm=r.ethylene_ppm,
            )
            timeline.append(SimulateTimelinePoint(
                t_hours=r.timestamp_h,
                temp_c=r.temp_c,
                humidity_pct=r.humidity_pct,
                co2_ppm=r.co2_ppm,
                ethylene_ppm=r.ethylene_ppm,
                methane_ppm=r.methane_ppm,
                rsl_days=r.days_until_spoilage,
                status=status,
            ))
    return SimulateResponse(timeline=timeline, model_version=settings.model_version)
