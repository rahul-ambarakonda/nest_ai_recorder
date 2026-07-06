from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass(slots=True)
class RecorderStats:
    started_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )
    events_total: int = 0
    clips_total: int = 0
    detections_by_type: dict[str, int] = field(default_factory=dict)
    last_event_at: str | None = None
    last_clip: str | None = None

    def record_event(self, event_type: str, timestamp: datetime) -> None:
        self.events_total += 1
        self.detections_by_type[event_type] = self.detections_by_type.get(event_type, 0) + 1
        self.last_event_at = timestamp.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    def record_clip(self, path: Path) -> None:
        self.clips_total += 1
        self.last_clip = str(path)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class StatsStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.stats = RecorderStats()

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.stats.to_dict(), indent=2), encoding="utf-8")

