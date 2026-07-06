from datetime import datetime, timezone
from pathlib import Path

from nest_ai_recorder.segments import (
    Segment,
    parse_segment,
    segment_filename,
    select_segments,
)


def test_segment_filename_uses_utc_timestamp() -> None:
    start = datetime(2026, 7, 6, 8, 30, tzinfo=timezone.utc)

    assert segment_filename("front_door", start) == "front_door_20260706T083000Z.mp4"


def test_parse_segment_returns_none_for_unrecognized_name() -> None:
    assert parse_segment(Path("front_door_latest.mp4"), 10) is None


def test_select_segments_returns_overlap_with_event_window() -> None:
    segments = [
        Segment(Path("a.mp4"), datetime(2026, 7, 6, 8, 29, 40, tzinfo=timezone.utc), 10),
        Segment(Path("b.mp4"), datetime(2026, 7, 6, 8, 29, 50, tzinfo=timezone.utc), 10),
        Segment(Path("c.mp4"), datetime(2026, 7, 6, 8, 30, 0, tzinfo=timezone.utc), 10),
        Segment(Path("d.mp4"), datetime(2026, 7, 6, 8, 30, 10, tzinfo=timezone.utc), 10),
    ]

    selected = select_segments(
        segments,
        datetime(2026, 7, 6, 8, 30, 0, tzinfo=timezone.utc),
        pre_seconds=10,
        post_seconds=10,
    )

    assert [segment.path.name for segment in selected] == ["b.mp4", "c.mp4"]

