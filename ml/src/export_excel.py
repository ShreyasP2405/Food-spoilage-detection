"""
Export a clean, Excel-friendly synthetic dataset over 30 days.

Columns are renamed to be explicit about which sensor each reading comes from.
Output: data/processed/banana_synthetic_30days_sensors.csv
"""
from __future__ import annotations

import csv
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .simulator import BananaSimulator, DEFAULT_DT_HOURS

OUT_PATH = Path(__file__).resolve().parents[2] / "data" / "processed" / "banana_synthetic_30days_sensors.csv"

REGIMES = {
    "cold_5C": lambda t: 5.0,
    "optimal_14C": lambda t: 14.0,
    "room_22C": lambda t: 22.0,
    "hot_32C": lambda t: 32.0,
    "dayNight_22pm5": lambda t: 22.0 + 5.0 * math.sin(2 * math.pi * t / 24.0),
}
RH_REGIMES = {"dry_50pct": 50.0, "moderate_70pct": 70.0, "optimal_92pct": 92.0}
INITIAL_RIPENESS = {"green_stage1": 1.2, "breaker_stage2": 2.0, "yellowing_stage3": 3.0}

HEADER = [
    "batch_id",
    "regime_temperature",
    "regime_humidity",
    "regime_initial_ripeness",
    "timestamp_utc",
    "elapsed_hours",
    "elapsed_days",
    "DHT22_temperature_C",
    "DHT22_humidity_percent",
    "MQ135_co2_ppm",
    "MQ135_ethylene_ppm",
    "MQ4_methane_ppm",
    "MQ135_raw_adc_0to1023",
    "MQ4_raw_adc_0to1023",
    "ripeness_stage_1to7",
    "predicted_days_until_spoilage",
    "traffic_light_status",
]


def main() -> dict:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    epoch = datetime(2026, 4, 1, 0, 0, 0, tzinfo=timezone.utc)
    total_hours = 24 * 30
    n_rows = 0
    n_batches = 0

    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(HEADER)

        for temp_name, temp_fn in REGIMES.items():
            for rh_name, rh in RH_REGIMES.items():
                for ripe_name, ripe in INITIAL_RIPENESS.items():
                    batch_id = f"{temp_name}__{rh_name}__{ripe_name}"
                    sim = BananaSimulator(
                        batch_id=batch_id,
                        initial_ripeness=ripe,
                        seed=hash(batch_id) % (2**32),
                    )
                    n_batches += 1
                    for reading in sim.stream(
                        total_hours=total_hours,
                        dt_h=DEFAULT_DT_HOURS,
                        temp_profile=temp_fn,
                        rh_profile=rh,
                        with_noise=True,
                    ):
                        d = reading.as_dict()
                        ts = (epoch + timedelta(hours=d["timestamp_h"])).strftime("%Y-%m-%d %H:%M:%S")
                        w.writerow([
                            batch_id,
                            temp_name,
                            rh_name,
                            ripe_name,
                            ts,
                            round(d["timestamp_h"], 2),
                            round(d["timestamp_h"] / 24.0, 3),
                            round(d["temp_c"], 2),
                            round(d["humidity_pct"], 2),
                            round(d["co2_ppm"], 1),
                            round(d["ethylene_ppm"], 4),
                            round(d["methane_ppm"], 4),
                            d["gas_mq135_raw"],
                            d["gas_mq4_raw"],
                            d["ripeness_estimate"],
                            round(d["days_until_spoilage"], 3),
                            d["status"],
                        ])
                        n_rows += 1

    return {"out_path": str(OUT_PATH), "n_batches": n_batches, "n_rows": n_rows}


if __name__ == "__main__":
    info = main()
    print(info)
