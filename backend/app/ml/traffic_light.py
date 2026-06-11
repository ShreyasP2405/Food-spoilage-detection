from __future__ import annotations

from typing import Literal

from app.core.schemas import ContributingFactor


Status = Literal["green", "yellow", "red"]


def classify(
    rsl_days: float,
    *,
    temp_c: float,
    humidity_pct: float,
    co2_ppm: float,
    methane_ppm: float,
    ethylene_ppm: float,
) -> tuple[Status, str, list[ContributingFactor]]:
    factors: list[ContributingFactor] = []

    if methane_ppm > 0.5:
        factors.append(ContributingFactor(
            name="methane",
            severity="critical",
            detail=f"Methane detected at {methane_ppm:.2f} ppm — anaerobic decomposition started.",
        ))
    if temp_c > 25.0:
        factors.append(ContributingFactor(
            name="temperature_high",
            severity="warning" if temp_c <= 30 else "critical",
            detail=f"Temperature {temp_c:.1f}°C exceeds typical storage; respiration accelerated.",
        ))
    if temp_c < 13.0:
        factors.append(ContributingFactor(
            name="chilling_injury",
            severity="warning",
            detail=f"Temperature {temp_c:.1f}°C below 13°C — risk of chilling injury (peel browning).",
        ))
    if humidity_pct < 80.0:
        factors.append(ContributingFactor(
            name="humidity_low",
            severity="warning",
            detail=f"Humidity {humidity_pct:.0f}% below optimal 90-95%; moisture loss likely.",
        ))
    if co2_ppm > 50_000:
        factors.append(ContributingFactor(
            name="co2_buildup",
            severity="warning",
            detail=f"CO2 {co2_ppm:.0f} ppm — ventilation recommended; nearing toxic 70k ppm.",
        ))
    if ethylene_ppm > 5.0:
        factors.append(ContributingFactor(
            name="ethylene_climacteric",
            severity="info",
            detail=f"Ethylene {ethylene_ppm:.1f} ppm — fruit at climacteric peak, ripening accelerating.",
        ))

    is_critical = any(f.severity == "critical" for f in factors)
    is_warning = any(f.severity == "warning" for f in factors)

    if is_critical or rsl_days <= 2.0:
        status: Status = "red"
        reason = factors[0].detail if factors else f"RSL {rsl_days:.1f}d ≤ 2 days; spoilage imminent."
    elif is_warning or rsl_days <= 5.0:
        status = "yellow"
        if factors:
            reason = factors[0].detail
        else:
            reason = f"RSL {rsl_days:.1f}d; conditions trending toward spoilage."
    else:
        status = "green"
        reason = f"Stable. RSL {rsl_days:.1f}d under current conditions."

    return status, reason, factors
