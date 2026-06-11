"""
Dataset generator for banana spoilage prediction.

Produces a CSV of (sensor_reading, days_until_spoilage, status) pairs across a
diverse grid of storage regimes:
  - cold (5C), optimal (14C), room (22C), hot (32C), and dynamic (sin day-night +- 5C)
  - humidity 50%, 70%, 92%
  - varied initial ripeness (1, 2, 3)
  - optional CO2-trapping events (low leak rate)
  - 30-min sampling, sensor noise on every reading

Split is later applied by batch_id so rows from the same banana never leak
between train/val/test.
"""

from __future__ import annotations

import csv
import math
from dataclasses import asdict
from pathlib import Path

import numpy as np

from .simulator import BananaSimulator, DEFAULT_DT_HOURS

OUT_PATH = Path(__file__).resolve().parents[2] / "data" / "processed" / "banana_synthetic_v1.csv"


TEMP_REGIMES = {
    "cold": lambda t: 5.0,
    "optimal": lambda t: 14.0,
    "room": lambda t: 22.0,
    "hot": lambda t: 32.0,
    "dynamic_room": lambda t: 22.0 + 5.0 * math.sin(2 * math.pi * t / 24.0),
    "dynamic_hot": lambda t: 28.0 + 5.0 * math.sin(2 * math.pi * t / 24.0),
}

RH_REGIMES = [50.0, 70.0, 92.0]
INITIAL_RIPENESS = [1.2, 2.0, 3.0]
LEAK_RATES = [0.15, 0.05]  # 0.05 = poorly ventilated container


CSV_HEADER = [
    "batch_id",
    "regime",
    "leak_rate",
    "initial_ripeness",
    "timestamp_h",
    "temp_c",
    "humidity_pct",
    "co2_ppm",
    "ethylene_ppm",
    "methane_ppm",
    "gas_mq135_raw",
    "gas_mq4_raw",
    "hours_since_harvest",
    "ripeness_estimate",
    "days_until_spoilage",
    "status",
]


def generate_dataset(
    out_path: Path = OUT_PATH,
    n_batches_per_combo: int = 4,
    max_hours: float = 24.0 * 30,
    seed: int = 42,
) -> dict:
    """
    Generate dataset; ~ len(TEMP_REGIMES) * len(RH_REGIMES) * len(INITIAL_RIPENESS)
    * len(LEAK_RATES) * n_batches_per_combo batches.
    With defaults: 6 * 3 * 3 * 2 * 4 = 432 batches.
    Each batch yields up to max_hours/0.5 = 1440 rows but stops near spoilage,
    averaging ~150 rows -> ~65k rows. Adjust n_batches_per_combo for size.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)

    n_rows = 0
    n_batches = 0
    rows_per_status = {"green": 0, "yellow": 0, "red": 0}

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(CSV_HEADER)

        for regime_name, temp_fn in TEMP_REGIMES.items():
            for rh in RH_REGIMES:
                for ripe in INITIAL_RIPENESS:
                    for leak in LEAK_RATES:
                        for k in range(n_batches_per_combo):
                            batch_id = f"{regime_name}_rh{int(rh)}_r{int(ripe*10)}_lk{int(leak*100)}_b{k}"
                            sim = BananaSimulator(
                                batch_id=batch_id,
                                initial_ripeness=ripe + float(rng.normal(0.0, 0.1)),
                                leak_rate_per_h=leak,
                                seed=int(rng.integers(0, 1_000_000)),
                            )
                            n_batches += 1
                            for reading in sim.stream(
                                total_hours=max_hours,
                                dt_h=DEFAULT_DT_HOURS,
                                temp_profile=temp_fn,
                                rh_profile=rh,
                                with_noise=True,
                            ):
                                d = reading.as_dict()
                                w.writerow([
                                    batch_id,
                                    regime_name,
                                    leak,
                                    ripe,
                                    d["timestamp_h"],
                                    d["temp_c"],
                                    d["humidity_pct"],
                                    d["co2_ppm"],
                                    d["ethylene_ppm"],
                                    d["methane_ppm"],
                                    d["gas_mq135_raw"],
                                    d["gas_mq4_raw"],
                                    d["hours_since_harvest"],
                                    d["ripeness_estimate"],
                                    d["days_until_spoilage"],
                                    d["status"],
                                ])
                                rows_per_status[d["status"]] = rows_per_status.get(d["status"], 0) + 1
                                n_rows += 1

    summary = {
        "out_path": str(out_path),
        "n_batches": n_batches,
        "n_rows": n_rows,
        "rows_per_status": rows_per_status,
    }
    return summary


if __name__ == "__main__":
    info = generate_dataset()
    print(info)
