# API Reference

OpenAPI/Swagger UI available at `http://localhost:8000/docs` once the backend is running. The endpoints below are the contract.

## `POST /api/predict`

Single-sample prediction.

**Request body**
```json
{
  "temp_c": 22.0,
  "humidity_pct": 70.0,
  "co2_ppm": 1500.0,
  "ethylene_ppm": 1.5,
  "methane_ppm": 0.0,
  "hours_since_harvest": 96.0,
  "ripeness_estimate": 3
}
```

**Response 200**
```json
{
  "rsl_days": 4.2,
  "status": "yellow",
  "confidence": 0.78,
  "model_version": "0.1.0",
  "reason": "Temperature 22.0°C exceeds typical storage; respiration accelerated.",
  "contributing_factors": [
    { "name": "temperature_high", "severity": "warning", "detail": "..." }
  ]
}
```

`status ∈ {green, yellow, red}`. Validation errors return `422`.

## `POST /api/predict-sequence`

Time-windowed prediction. Use this when the LSTM is loaded — a 48-step sliding window (24 h at 30-min sampling) gives the most accurate result.

**Request body** — `{ "readings": [SensorReading × 1..512] }`. `SensorReading` is the same shape as the predict request plus optional `timestamp` and `batch_id`.

## `GET /api/simulate`

Run the physics simulator forward with constant conditions and return the full timeline. Used by the frontend's fast-forward mode.

```
GET /api/simulate?temp_c=22&humidity_pct=70&hours=168&initial_ripeness=2.0&sample_every_h=3.0
```

**Response 200** — `{ "timeline": [SimulateTimelinePoint], "model_version": "0.1.0" }`

## `WS /ws/stream`

WebSocket. Connect with conditions in the query string:

```
ws://localhost:8000/ws/stream?temp_c=22&humidity_pct=70&initial_ripeness=2.0&tick_seconds=1
```

The server pushes a frame every `tick_seconds`:

```json
{
  "reading": { "timestamp_h": ..., "temp_c": ..., "co2_ppm": ..., ... },
  "prediction": { "rsl_days": ..., "status": "yellow", "reason": "...", "contributing_factors": [...] }
}
```

## `GET /api/health`

```json
{ "status": "ok", "model_loaded": true, "model_kind": "rf", "model_version": "0.1.0" }
```

## `GET /api/reference/banana`

Returns the contents of `data/references/banana_postharvest_constants.json` for the frontend to draw "optimal-range" markers on charts.
