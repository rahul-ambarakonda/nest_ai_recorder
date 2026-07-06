from datetime import datetime, timedelta, timezone

from nest_ai_recorder.events import DetectionEvent, EventDeduplicator


def test_event_deduplicator_suppresses_within_cooldown() -> None:
    deduplicator = EventDeduplicator(cooldown_seconds=90)
    first = DetectionEvent(
        event_type="person",
        camera="front_door",
        timestamp=datetime(2026, 7, 6, 8, 30, tzinfo=timezone.utc),
        confidence=0.82,
        track_id="person-1",
    )
    duplicate = DetectionEvent(
        event_type="person",
        camera="front_door",
        timestamp=first.timestamp + timedelta(seconds=30),
        confidence=0.91,
        track_id="person-1",
    )

    assert deduplicator.should_emit(first) is True
    assert deduplicator.should_emit(duplicate) is False


def test_event_deduplicator_allows_after_cooldown() -> None:
    deduplicator = EventDeduplicator(cooldown_seconds=90)
    first = DetectionEvent(
        event_type="person",
        camera="front_door",
        timestamp=datetime(2026, 7, 6, 8, 30, tzinfo=timezone.utc),
        confidence=0.82,
    )
    later = DetectionEvent(
        event_type="person",
        camera="front_door",
        timestamp=first.timestamp + timedelta(seconds=91),
        confidence=0.88,
    )

    assert deduplicator.should_emit(first) is True
    assert deduplicator.should_emit(later) is True

