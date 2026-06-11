from fastapi.testclient import TestClient

from app.main import create_app


def _client():
    app = create_app()
    return TestClient(app)


def test_health_returns_ok():
    with _client() as c:
        r = c.get("/api/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert "model_kind" in body


def test_predict_happy_path():
    with _client() as c:
        body = {
            "temp_c": 22.0, "humidity_pct": 70.0, "co2_ppm": 1500.0,
            "ethylene_ppm": 1.5, "methane_ppm": 0.0,
            "hours_since_harvest": 96.0, "ripeness_estimate": 3,
        }
        r = c.post("/api/predict", json=body)
        assert r.status_code == 200
        d = r.json()
        assert d["status"] in ("green", "yellow", "red")
        assert d["rsl_days"] >= 0.0


def test_predict_validation_error():
    with _client() as c:
        body = {"temp_c": 999, "humidity_pct": 70, "co2_ppm": 1500,
                "hours_since_harvest": 1, "ripeness_estimate": 3}
        r = c.post("/api/predict", json=body)
        assert r.status_code == 422


def test_simulate_returns_timeline():
    with _client() as c:
        r = c.get("/api/simulate", params={"temp_c": 22.0, "humidity_pct": 70.0, "hours": 48})
        assert r.status_code == 200
        d = r.json()
        assert "timeline" in d and len(d["timeline"]) > 0
        first = d["timeline"][0]
        assert "rsl_days" in first and "status" in first


def test_reference_returns_constants():
    with _client() as c:
        r = c.get("/api/reference/banana")
        assert r.status_code == 200
        c_dict = r.json()["constants"]
        assert c_dict["commodity"] == "banana_cavendish"
