from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterator


class DataSource(ABC):
    """Abstract sensor data source.

    Concrete sources:
      - SimulatedDataSource: physics simulator (current MVP)
      - MqttDataSource: real ESP32 over MQTT (future)
    """

    @abstractmethod
    async def stream(self) -> AsyncIterator[dict]:
        """Yield SensorReading dicts indefinitely until cancelled."""
        ...

    @abstractmethod
    async def close(self) -> None:
        ...
