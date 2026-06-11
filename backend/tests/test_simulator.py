from ml.src.simulator import BananaSimulator, arrhenius_factor, climacteric_multiplier


def test_arrhenius_monotonic_with_temperature():
    assert arrhenius_factor(5) < arrhenius_factor(14) < arrhenius_factor(30)


def test_climacteric_peaks_around_stage_5():
    peak = climacteric_multiplier(5.0)
    assert peak > climacteric_multiplier(2.0)
    assert peak > climacteric_multiplier(7.0)
    assert 5.0 < peak < 6.0


def test_simulator_is_deterministic_with_seed():
    a = BananaSimulator(seed=123)
    b = BananaSimulator(seed=123)
    a.state.temp_c = b.state.temp_c = 22.0
    a.state.rh_pct = b.state.rh_pct = 70.0
    rs_a = [a.read_sensor() for _ in range(5)]
    rs_b = [b.read_sensor() for _ in range(5)]
    for x, y in zip(rs_a, rs_b):
        assert x.co2_ppm == y.co2_ppm
        assert x.temp_c == y.temp_c


def test_higher_temp_shortens_shelf_life():
    cold = BananaSimulator(seed=1)
    cold.state.temp_c = 14.0
    cold.state.rh_pct = 92.0
    hot = BananaSimulator(seed=1)
    hot.state.temp_c = 32.0
    hot.state.rh_pct = 92.0
    assert cold.estimate_days_until_spoilage() > hot.estimate_days_until_spoilage()


def test_eventually_spoils_at_room_temperature():
    sim = BananaSimulator(seed=2, initial_ripeness=3.0)
    spoiled = False
    for _ in sim.stream(total_hours=24 * 20, dt_h=0.5, temp_profile=22.0, rh_profile=65.0):
        if sim.state.is_spoiled:
            spoiled = True
            break
    assert spoiled, "Banana at 22C/65% RH should spoil within 20 days"
