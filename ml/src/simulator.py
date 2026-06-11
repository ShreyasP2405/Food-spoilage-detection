"""
Physics-based banana spoilage simulator (Cavendish, Musa acuminata AAA).

Calibrated to published post-harvest constants in
data/references/banana_postharvest_constants.json.

Models:
  - Arrhenius temperature dependence of respiration
  - Climacteric ripening curve with autocatalytic ethylene
  - Humidity stress on biological aging clock
  - Container gas accumulation (production - leak)
  - Anaerobic methane onset on late-stage spoilage
  - Sensor noise + analog MQ-sensor responses

The simulator is the single source of truth for synthetic training data and
for the live preview the backend serves to the frontend. The same class is
imported from ml/src and used inside the FastAPI process.
"""

from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

import numpy as np

R_GAS = 8.314
EA_J_PER_MOL = 80_000.0
T_REF_C = 14.0
DEFAULT_DT_HOURS = 0.5  # 30 min sampling

_CONSTANTS_PATH = Path(__file__).resolve().parents[2] / "data" / "references" / "banana_postharvest_constants.json"


def load_constants() -> dict:
    with open(_CONSTANTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def arrhenius_factor(temp_c: float, t_ref_c: float = T_REF_C, ea: float = EA_J_PER_MOL) -> float:
    """Arrhenius rate multiplier relative to T_REF."""
    t_k = temp_c + 273.15
    t_ref_k = t_ref_c + 273.15
    return math.exp(-ea / R_GAS * (1.0 / t_k - 1.0 / t_ref_k))


def climacteric_multiplier(ripeness: float) -> float:
    """
    Piecewise climacteric respiration multiplier vs ripeness stage 1..7.
    Low pre-climacteric -> sharp rise to peak ~stage 5 -> drop -> senescence rise.
    Peak ~5.5x calibrated so 10 mg/kg/h base * 5.5 = 55 mg/kg/h, matching
    published 56.8 mg CO2/kg/h climacteric peak.
    """
    r = max(1.0, min(7.5, ripeness))
    if r <= 3.0:
        # 1.0 at stage 1 -> 1.4 at stage 3
        return 1.0 + 0.2 * (r - 1.0)
    if r <= 5.0:
        # 1.4 at 3 -> 5.5 at 5 (climacteric rise)
        return 1.4 + (5.5 - 1.4) * (r - 3.0) / 2.0
    if r <= 6.5:
        # 5.5 at 5 -> 2.5 at 6.5 (post-climacteric drop)
        return 5.5 - (5.5 - 2.5) * (r - 5.0) / 1.5
    # 2.5 at 6.5 -> 4.0 at 7.5 (senescence rise from microbial activity)
    return 2.5 + (4.0 - 2.5) * (r - 6.5) / 1.0


def ethylene_curve(ripeness: float) -> float:
    """Ethylene production uL/kg/h vs ripeness, peaks at climacteric ~stage 5."""
    r = max(1.0, min(7.5, ripeness))
    if r <= 3.0:
        return 0.1 + 0.3 * (r - 1.0) / 2.0  # nearly nothing pre-climacteric
    if r <= 5.0:
        return 0.4 + (7.4 - 0.4) * (r - 3.0) / 2.0  # rise to peak 7.4
    if r <= 6.5:
        return 7.4 - (7.4 - 1.0) * (r - 5.0) / 1.5  # post-climacteric decline
    return 1.0


def humidity_stress_factor(rh_pct: float) -> float:
    """Deviation from 92.5% RH increases biological stress."""
    return 1.0 + 0.02 * abs(rh_pct - 92.5)


def aging_rate(temp_c: float, rh_pct: float) -> float:
    """How fast the biological clock advances at current conditions, vs reference."""
    return arrhenius_factor(temp_c) * humidity_stress_factor(rh_pct)


@dataclass
class BatchState:
    batch_id: str
    t_hours: float = 0.0
    temp_c: float = T_REF_C
    rh_pct: float = 92.5
    ripeness_stage: float = 1.0
    cumulative_stress: float = 0.0
    co2_ppm: float = 420.0          # ambient atmospheric baseline
    ethylene_ppm: float = 0.0
    methane_ppm: float = 0.0
    is_spoiled: bool = False
    mass_kg: float = 1.5
    container_volume_m3: float = 0.05
    leak_rate_per_h: float = 0.15
    rng: random.Random = field(default_factory=random.Random)


@dataclass
class SimReading:
    timestamp_h: float
    batch_id: str
    temp_c: float
    humidity_pct: float
    co2_ppm: float
    ethylene_ppm: float
    methane_ppm: float
    gas_mq135_raw: int
    gas_mq4_raw: int
    hours_since_harvest: float
    ripeness_estimate: int
    days_until_spoilage: float
    status: str

    def as_dict(self) -> dict:
        return {
            "timestamp_h": round(self.timestamp_h, 3),
            "batch_id": self.batch_id,
            "temp_c": round(self.temp_c, 3),
            "humidity_pct": round(self.humidity_pct, 3),
            "co2_ppm": round(self.co2_ppm, 2),
            "ethylene_ppm": round(self.ethylene_ppm, 4),
            "methane_ppm": round(self.methane_ppm, 4),
            "gas_mq135_raw": self.gas_mq135_raw,
            "gas_mq4_raw": self.gas_mq4_raw,
            "hours_since_harvest": round(self.hours_since_harvest, 3),
            "ripeness_estimate": self.ripeness_estimate,
            "days_until_spoilage": round(self.days_until_spoilage, 4),
            "status": self.status,
        }


class BananaSimulator:
    """Physics-grounded synthetic sensor stream for one banana batch."""

    BASE_CO2_MG_PER_KG_H = 10.0  # respiration at 14C, ripeness 1
    STRESS_THRESHOLD = 1500.0    # arbitrary integral units; spoilage when exceeded
    METHANE_ONSET_RIPENESS = 7.2

    def __init__(
        self,
        batch_id: str = "banana_lot_001",
        initial_ripeness: float = 1.5,
        mass_kg: float = 1.5,
        container_volume_m3: float = 0.05,
        leak_rate_per_h: float = 0.15,
        seed: int | None = None,
    ) -> None:
        self.constants = load_constants()
        self.state = BatchState(
            batch_id=batch_id,
            ripeness_stage=initial_ripeness,
            mass_kg=mass_kg,
            container_volume_m3=container_volume_m3,
            leak_rate_per_h=leak_rate_per_h,
            rng=random.Random(seed),
        )

    # ----- physics -----

    def _co2_production_mg_per_h(self) -> float:
        rate_per_kg = (
            self.BASE_CO2_MG_PER_KG_H
            * arrhenius_factor(self.state.temp_c)
            * climacteric_multiplier(self.state.ripeness_stage)
        )
        return rate_per_kg * self.state.mass_kg

    def _ethylene_production_uL_per_h(self) -> float:
        return ethylene_curve(self.state.ripeness_stage) * arrhenius_factor(self.state.temp_c) * self.state.mass_kg

    def _methane_production_ppm_per_h(self) -> float:
        if self.state.ripeness_stage < self.METHANE_ONSET_RIPENESS:
            return 0.0
        # rapid anaerobic methane buildup once tissue collapse begins
        return 2.5 * (self.state.ripeness_stage - self.METHANE_ONSET_RIPENESS + 0.1)

    def _step_gases(self, dt_h: float) -> None:
        # CO2: production (mg/h) -> ppm in container volume
        # 1 mol CO2 = 44.01 g, ideal-gas approx: ppm ~ (mg / volume_m3) / (1.964 mg/m3 per ppm at STP) ~ approx
        # We use a simpler scaling calibrated to plausible rise rates in a 50L sealed box.
        co2_prod_mg_h = self._co2_production_mg_per_h()
        co2_prod_ppm_h = co2_prod_mg_h / (self.state.container_volume_m3 * 1.964)
        self.state.co2_ppm += dt_h * (co2_prod_ppm_h - self.state.leak_rate_per_h * (self.state.co2_ppm - 420.0))

        ethylene_prod_uL_h = self._ethylene_production_uL_per_h()
        # 1 uL gas in V m3 ~ 1e-3 / V ppm (approx, room T)
        ethylene_prod_ppm_h = ethylene_prod_uL_h / (self.state.container_volume_m3 * 1000.0)
        self.state.ethylene_ppm += dt_h * (ethylene_prod_ppm_h - self.state.leak_rate_per_h * self.state.ethylene_ppm)

        methane_prod_ppm_h = self._methane_production_ppm_per_h()
        self.state.methane_ppm += dt_h * (methane_prod_ppm_h - self.state.leak_rate_per_h * self.state.methane_ppm)

        # numerical guards
        self.state.co2_ppm = max(420.0, self.state.co2_ppm)
        self.state.ethylene_ppm = max(0.0, self.state.ethylene_ppm)
        self.state.methane_ppm = max(0.0, self.state.methane_ppm)

    def _step_aging(self, dt_h: float) -> None:
        rate = aging_rate(self.state.temp_c, self.state.rh_pct)
        # ripeness advances ~1 stage per 36h at reference conditions
        self.state.ripeness_stage += dt_h * rate / 36.0

        # cumulative stress from out-of-spec conditions
        temp_dev = max(0.0, self.state.temp_c - 18.0) + max(0.0, 8.0 - self.state.temp_c)
        rh_dev = max(0.0, 80.0 - self.state.rh_pct) + max(0.0, self.state.rh_pct - 98.0)
        co2_pen = max(0.0, self.state.co2_ppm - 50_000.0) / 5_000.0
        self.state.cumulative_stress += dt_h * (temp_dev**1.5 + 0.5 * rh_dev + co2_pen)

        if (
            self.state.ripeness_stage >= 7.0
            or self.state.cumulative_stress > self.STRESS_THRESHOLD
            or self.state.methane_ppm > 1.0
        ):
            self.state.is_spoiled = True

    def _classify_status(self, days_left: float) -> str:
        if self.state.is_spoiled or self.state.methane_ppm > 0.5 or days_left <= 2.0:
            return "red"
        if days_left <= 5.0 or self.state.temp_c > 20.0 or self.state.rh_pct < 80.0:
            return "yellow"
        return "green"

    def step(self, dt_h: float = DEFAULT_DT_HOURS, temp_c: float | None = None, rh_pct: float | None = None) -> None:
        if temp_c is not None:
            self.state.temp_c = temp_c
        if rh_pct is not None:
            self.state.rh_pct = rh_pct
        self._step_gases(dt_h)
        self._step_aging(dt_h)
        self.state.t_hours += dt_h

    # ----- forward shelf-life estimation (ground truth label) -----

    def estimate_days_until_spoilage(self, max_days: float = 30.0) -> float:
        """Project forward from current state with held-constant conditions and return days until spoiled."""
        if self.state.is_spoiled:
            return 0.0
        snap = BatchState(
            batch_id=self.state.batch_id,
            t_hours=self.state.t_hours,
            temp_c=self.state.temp_c,
            rh_pct=self.state.rh_pct,
            ripeness_stage=self.state.ripeness_stage,
            cumulative_stress=self.state.cumulative_stress,
            co2_ppm=self.state.co2_ppm,
            ethylene_ppm=self.state.ethylene_ppm,
            methane_ppm=self.state.methane_ppm,
            is_spoiled=False,
            mass_kg=self.state.mass_kg,
            container_volume_m3=self.state.container_volume_m3,
            leak_rate_per_h=self.state.leak_rate_per_h,
        )
        ghost = BananaSimulator.__new__(BananaSimulator)
        ghost.constants = self.constants
        ghost.state = snap

        max_steps = int(max_days * 24.0 / DEFAULT_DT_HOURS)
        elapsed_h = 0.0
        for _ in range(max_steps):
            ghost._step_gases(DEFAULT_DT_HOURS)
            ghost._step_aging(DEFAULT_DT_HOURS)
            elapsed_h += DEFAULT_DT_HOURS
            if ghost.state.is_spoiled:
                return elapsed_h / 24.0
        return max_days  # capped horizon

    # ----- sensor read with noise -----

    def read_sensor(self, with_noise: bool = True) -> SimReading:
        rng = self.state.rng
        temp_obs = self.state.temp_c + (rng.gauss(0.0, 0.3) if with_noise else 0.0)
        rh_obs = max(0.0, min(100.0, self.state.rh_pct + (rng.gauss(0.0, 2.0) if with_noise else 0.0)))
        co2_obs = max(0.0, self.state.co2_ppm + (rng.gauss(0.0, 30.0) if with_noise else 0.0))
        eth_obs = max(0.0, self.state.ethylene_ppm + (rng.gauss(0.0, 0.05) if with_noise else 0.0))
        ch4_obs = max(0.0, self.state.methane_ppm + (rng.gauss(0.0, 0.02) if with_noise else 0.0))

        # MQ-135 raw 0..1023 — non-linear curve to CO2/NH3 surrogate
        mq135 = int(min(1023, 80 + 0.04 * co2_obs + 5.0 * eth_obs + (rng.gauss(0.0, 4.0) if with_noise else 0.0)))
        # MQ-4 — methane sensitive
        mq4 = int(min(1023, 60 + 60.0 * ch4_obs + 0.005 * co2_obs + (rng.gauss(0.0, 3.0) if with_noise else 0.0)))

        days_left = self.estimate_days_until_spoilage()
        status = self._classify_status(days_left)
        return SimReading(
            timestamp_h=self.state.t_hours,
            batch_id=self.state.batch_id,
            temp_c=temp_obs,
            humidity_pct=rh_obs,
            co2_ppm=co2_obs,
            ethylene_ppm=eth_obs,
            methane_ppm=ch4_obs,
            gas_mq135_raw=max(0, mq135),
            gas_mq4_raw=max(0, mq4),
            hours_since_harvest=self.state.t_hours,
            ripeness_estimate=int(round(max(1, min(7, self.state.ripeness_stage)))),
            days_until_spoilage=days_left,
            status=status,
        )

    # ----- iterators -----

    def stream(
        self,
        total_hours: float,
        dt_h: float = DEFAULT_DT_HOURS,
        temp_profile=None,
        rh_profile=None,
        with_noise: bool = True,
    ) -> Iterator[SimReading]:
        """
        Yield readings every dt_h hours for total_hours.
        temp_profile / rh_profile: callables (t_h) -> float, or constants, or None to keep current.
        """
        steps = int(total_hours / dt_h)
        for _ in range(steps):
            t = self.state.t_hours
            new_t = temp_profile(t) if callable(temp_profile) else temp_profile
            new_rh = rh_profile(t) if callable(rh_profile) else rh_profile
            self.step(dt_h=dt_h, temp_c=new_t, rh_pct=new_rh)
            yield self.read_sensor(with_noise=with_noise)
            if self.state.is_spoiled:
                # keep streaming a bit after spoilage so methane curve is captured
                if self.state.ripeness_stage > 7.5:
                    return
