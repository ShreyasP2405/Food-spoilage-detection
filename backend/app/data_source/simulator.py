from __future__ import annotations

import asyncio
from typing import AsyncIterator

from ml.src.simulator import BananaSimulator, DEFAULT_DT_HOURS

from .base import DataSource


class SimulatedDataSource(DataSource):
    """Wraps the physics simulator and emits a SensorReading every `tick_seconds`
    of real time, advancing the simulation by `dt_h` simulated hours per tick.

    Default mapping: 1 real second -> 30 simulated minutes.
    """

    def __init__(
        self,
        temp_c: float = 22.0,
        humidity_pct: float = 70.0,
        initial_ripeness: float = 2.0,
        dt_h: float = DEFAULT_DT_HOURS,
        tick_seconds: float = 1.0,
        seed: int | None = None,
        batch_id: str = "live_sim_001",
    ) -> None:
        self.sim = BananaSimulator(batch_id=batch_id, initial_ripeness=initial_ripeness, seed=seed)
        self.sim.state.temp_c = temp_c
        self.sim.state.rh_pct = humidity_pct
        self.dt_h = dt_h
        self.tick_seconds = tick_seconds
        self._closed = False

    async def stream(self) -> AsyncIterator[dict]:
        while not self._closed:
            self.sim.step(dt_h=self.dt_h)
            r = self.sim.read_sensor()
            yield r.as_dict()
            try:
                await asyncio.sleep(self.tick_seconds)
            except asyncio.CancelledError:
                break

    async def close(self) -> None:
        self._closed = True
