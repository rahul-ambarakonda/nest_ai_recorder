from __future__ import annotations

from datetime import datetime
from pathlib import Path

from nest_ai_recorder.segments import Segment, select_segments


def clip_output_path(base_directory: Path, event_type: str, event_time: datetime) -> Path:
    month_dir = event_time.strftime("%m-%Y")
    day_dir = event_time.strftime("%d-%m-%Y")
    filename = f"{event_type}_{event_time.strftime('%Y%m%d_%H%M%S')}.mp4"
    return base_directory / month_dir / day_dir / filename


def plan_clip_segments(
    segments: list[Segment],
    event_time: datetime,
    pre_buffer_seconds: int,
    post_buffer_seconds: int,
) -> list[Path]:
    return [
        segment.path
        for segment in select_segments(
            segments,
            event_time,
            pre_buffer_seconds,
            post_buffer_seconds,
        )
    ]

