from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from nest_ai_recorder.detection import Detection


@dataclass(frozen=True, slots=True)
class DetectionEvent:
    event_type: str
    camera: str
    timestamp: datetime
    confidence: float
    track_id: str | None = None


class EventDeduplicator:
    def __init__(self, cooldown_seconds: int) -> None:
        self.cooldown = timedelta(seconds=cooldown_seconds)
        self._last_seen: dict[tuple[str, str, str | None], datetime] = {}

    def should_emit(self, event: DetectionEvent) -> bool:
        timestamp = event.timestamp.astimezone(timezone.utc)
        key = (event.camera, event.event_type, event.track_id)
        last_seen = self._last_seen.get(key)
        if last_seen is not None and timestamp - last_seen < self.cooldown:
            return False
        self._last_seen[key] = timestamp
        return True


def event_from_detection(detection: Detection, camera: str, timestamp: datetime) -> DetectionEvent:
    return DetectionEvent(
        event_type=detection.label,
        camera=camera,
        timestamp=timestamp,
        confidence=detection.confidence,
        track_id=detection.track_id,
    )
