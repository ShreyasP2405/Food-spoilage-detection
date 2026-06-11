from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, ConfigDict


Status = Literal["green", "yellow", "red"]


class SensorReading(BaseModel):
    model_config = ConfigDict(extra="forbid")
    timestamp: str | None = Field(None, description="ISO-8601, optional. If absent, server time is used.")
    batch_id: str = "banana_lot_001"
    temp_c: float = Field(..., ge=-20.0, le=60.0)
    humidity_pct: float = Field(..., ge=0.0, le=100.0)
    co2_ppm: float = Field(..., ge=300.0, le=200_000.0)
    ethylene_ppm: float = Field(0.0, ge=0.0, le=500.0)
    methane_ppm: float = Field(0.0, ge=0.0, le=500.0)
    gas_mq135_raw: int = Field(0, ge=0, le=1023)
    gas_mq4_raw: int = Field(0, ge=0, le=1023)
    hours_since_harvest: float = Field(0.0, ge=0.0, le=24 * 60)
    ripeness_estimate: int = Field(1, ge=1, le=7)


class PredictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    temp_c: float = Field(..., ge=-20.0, le=60.0)
    humidity_pct: float = Field(..., ge=0.0, le=100.0)
    co2_ppm: float = Field(..., ge=300.0, le=200_000.0)
    ethylene_ppm: float = Field(0.0, ge=0.0, le=500.0)
    methane_ppm: float = Field(0.0, ge=0.0, le=500.0)
    hours_since_harvest: float = Field(0.0, ge=0.0, le=24 * 60)
    ripeness_estimate: int = Field(1, ge=1, le=7)


class ContributingFactor(BaseModel):
    name: str
    severity: Literal["info", "warning", "critical"]
    detail: str


class PredictionResponse(BaseModel):
    rsl_days: float = Field(..., description="Remaining Shelf Life in days.")
    status: Status
    confidence: float = Field(..., ge=0.0, le=1.0)
    model_version: str
    reason: str
    contributing_factors: list[ContributingFactor] = []


class PredictSequenceRequest(BaseModel):
    readings: list[SensorReading] = Field(..., min_length=1, max_length=512)


class SimulateTimelinePoint(BaseModel):
    t_hours: float
    temp_c: float
    humidity_pct: float
    co2_ppm: float
    ethylene_ppm: float
    methane_ppm: float
    rsl_days: float
    status: Status


class SimulateResponse(BaseModel):
    timeline: list[SimulateTimelinePoint]
    model_version: str


class HealthResponse(BaseModel):
    status: Literal["ok"]
    model_loaded: bool
    model_kind: Literal["lstm", "rf", "none"]
    model_version: str


class ReferenceResponse(BaseModel):
    constants: dict
