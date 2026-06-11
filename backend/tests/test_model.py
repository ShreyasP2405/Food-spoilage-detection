from app.ml.traffic_light import classify
from app.ml.preprocess import clamp_features, FEATURE_ORDER


def test_traffic_light_red_on_methane():
    s, reason, factors = classify(
        rsl_days=10.0, temp_c=14.0, humidity_pct=92.0, co2_ppm=500.0,
        methane_ppm=1.0, ethylene_ppm=0.5,
    )
    assert s == "red"
    assert any(f.name == "methane" for f in factors)


def test_traffic_light_red_on_low_rsl():
    s, _, _ = classify(rsl_days=1.5, temp_c=14, humidity_pct=92, co2_ppm=500, methane_ppm=0, ethylene_ppm=0)
    assert s == "red"


def test_traffic_light_yellow_when_temp_warm():
    s, _, _ = classify(rsl_days=10, temp_c=27, humidity_pct=85, co2_ppm=500, methane_ppm=0, ethylene_ppm=0)
    assert s == "yellow"


def test_traffic_light_green_under_optimal_conditions():
    s, _, _ = classify(rsl_days=14, temp_c=14, humidity_pct=92, co2_ppm=500, methane_ppm=0, ethylene_ppm=0)
    assert s == "green"


def test_clamp_pushes_extreme_values_inside_range():
    out, warns = clamp_features({
        "temp_c": -50.0, "humidity_pct": 200.0, "co2_ppm": 1_000_000.0,
        "ethylene_ppm": -1.0, "methane_ppm": -1.0,
        "hours_since_harvest": 99999.0, "ripeness_estimate": 99,
    })
    for k in FEATURE_ORDER:
        assert k in out
    assert len(warns) >= 4
