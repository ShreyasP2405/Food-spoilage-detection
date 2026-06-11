from __future__ import annotations

import numpy as np

FEATURE_ORDER = [
    "temp_c",
    "humidity_pct",
    "co2_ppm",
    "ethylene_ppm",
    "methane_ppm",
    "hours_since_harvest",
    "ripeness_estimate",
]

# Training-data observed ranges, used to clamp inputs that fall outside training distribution.
CLAMP_RANGES = {
    "temp_c": (-5.0, 45.0),
    "humidity_pct": (30.0, 100.0),
    "co2_ppm": (300.0, 100_000.0),
    "ethylene_ppm": (0.0, 200.0),
    "methane_ppm": (0.0, 200.0),
    "hours_since_harvest": (0.0, 720.0),
    "ripeness_estimate": (1.0, 7.0),
}


def features_to_vector(d: dict) -> np.ndarray:
    return np.asarray([float(d[k]) for k in FEATURE_ORDER], dtype=np.float32)


def clamp_features(d: dict) -> tuple[dict, list[str]]:
    out, warns = dict(d), []
    for k, (lo, hi) in CLAMP_RANGES.items():
        v = float(out[k])
        if v < lo:
            warns.append(f"{k} below training range ({v} < {lo}); clamped")
            out[k] = lo
        elif v > hi:
            warns.append(f"{k} above training range ({v} > {hi}); clamped")
            out[k] = hi
    return out, warns
