"""
Placeholder MQTT data source for the future ESP32 ingest path.

When real hardware comes online:
  - subscribe to topic e.g. `bss/{batch_id}/reading`
  - decode JSON or compact binary payload from ESP32
  - convert raw MQ-135 / MQ-4 ADC counts to ppm via standard MQ load-line
    calibration (datasheet: log10(Rs/R0) -> log10(ppm))
  - emit a SensorReading dict identical to the one the simulator produces.

The rest of the system does not change.
"""
from __future__ import annotations

from typing import AsyncIterator

from .base import DataSource


class MqttDataSource(DataSource):
    def __init__(self, broker_url: str, topic: str) -> None:
        self.broker_url = broker_url
        self.topic = topic

    async def stream(self) -> AsyncIterator[dict]:
        raise NotImplementedError(
            "MqttDataSource is a stub. Hardware integration is post-MVP. "
            "Implement an asyncio MQTT client (e.g. aiomqtt) here."
        )
        if False:  # pragma: no cover -- typing aid
            yield {}

    async def close(self) -> None:
        return None
