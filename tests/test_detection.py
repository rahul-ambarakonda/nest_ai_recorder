from nest_ai_recorder.config import DetectionConfig
from nest_ai_recorder.detection import Detection, IouTracker, ZoneFilter
from nest_ai_recorder.geometry import Box, Point, point_in_polygon


def test_point_in_polygon() -> None:
    polygon = [Point(0, 0), Point(10, 0), Point(10, 10), Point(0, 10)]

    assert point_in_polygon(Point(5, 5), polygon) is True
    assert point_in_polygon(Point(15, 5), polygon) is False


def test_zone_filter_rejects_ignore_zone() -> None:
    config = DetectionConfig(
        confidence=0.5,
        object_classes=["person"],
        ignore_zones=[[(0, 0), (100, 0), (100, 100), (0, 100)]],
    )
    zone_filter = ZoneFilter(config)
    detection = Detection("person", 0.9, Box(10, 10, 20, 20))

    assert zone_filter.filter([detection]) == []


def test_zone_filter_requires_detection_zone_when_configured() -> None:
    config = DetectionConfig(
        confidence=0.5,
        object_classes=["person"],
        detection_zones=[[(0, 0), (100, 0), (100, 100), (0, 100)]],
    )
    zone_filter = ZoneFilter(config)

    inside = Detection("person", 0.9, Box(10, 10, 20, 20))
    outside = Detection("person", 0.9, Box(150, 150, 170, 170))

    assert zone_filter.filter([inside, outside]) == [inside]


def test_iou_tracker_keeps_id_for_overlapping_detection() -> None:
    tracker = IouTracker(iou_threshold=0.2)
    first = tracker.update([Detection("person", 0.9, Box(0, 0, 100, 100))])
    second = tracker.update([Detection("person", 0.9, Box(10, 10, 110, 110))])

    assert first[0].track_id == second[0].track_id
