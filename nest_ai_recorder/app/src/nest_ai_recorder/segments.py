from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path


SEGMENT_TIME_FORMAT = "%Y%m%dT%H%M%SZ"


@dataclass(frozen=True, slots=True)
class Segment:
    path: Path
    start: datetime
    duration_seconds: int

    @property
    def end(self) -> datetime:
        return self.start + timedelta(seconds=self.duration_seconds)


def segment_filename(camera_name: str, start: datetime) -> str:
    utc_start = start.astimezone(timezone.utc)
    return f"{camera_name}_{utc_start.strftime(SEGMENT_TIME_FORMAT)}.mp4"


def parse_segment(path: Path, segment_seconds: int) -> Segment | None:
    stem_parts = path.stem.rsplit("_", 1)
    if len(stem_parts) != 2:
        return None

    try:
        start = datetime.strptime(stem_parts[1], SEGMENT_TIME_FORMAT).replace(
            tzinfo=timezone.utc
        )
    except ValueError:
        return None

    return Segment(path=path, start=start, duration_seconds=segment_seconds)


def discover_segments(directory: Path, segment_seconds: int) -> list[Segment]:
    if not directory.exists():
        return []

    segments = [
        segment
        for pattern in ("*.ts", "*.mp4")
        for path in directory.glob(pattern)
        if (segment := parse_segment(path, segment_seconds)) is not None
    ]
    return sorted(segments, key=lambda item: item.start)


def select_segments(
    segments: list[Segment],
    event_time: datetime,
    pre_seconds: int,
    post_seconds: int,
) -> list[Segment]:
    event_utc = event_time.astimezone(timezone.utc)
    wanted_start = event_utc - timedelta(seconds=pre_seconds)
    wanted_end = event_utc + timedelta(seconds=post_seconds)

    return [
        segment
        for segment in segments
        if segment.start < wanted_end and segment.end > wanted_start
    ]

