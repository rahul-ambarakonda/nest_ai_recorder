from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol

from nest_ai_recorder.config import DetectionConfig
from nest_ai_recorder.geometry import Box, polygon_from_tuples, point_in_polygon


@dataclass(frozen=True, slots=True)
class Detection:
    label: str
    confidence: float
    box: Box
    track_id: str | None = None


@dataclass(frozen=True, slots=True)
class FrameDetections:
    timestamp: datetime
    detections: list[Detection]
    motion_score: float = 0.0


class ObjectDetector(Protocol):
    def detect(self, frame: Any, timestamp: datetime) -> FrameDetections:
        ...


class ZoneFilter:
    def __init__(self, config: DetectionConfig) -> None:
        self.config = config
        self.ignore_zones = [polygon_from_tuples(zone) for zone in config.ignore_zones]
        self.detection_zones = [polygon_from_tuples(zone) for zone in config.detection_zones]

    def allows(self, detection: Detection) -> bool:
        center = detection.box.centroid
        if any(point_in_polygon(center, zone) for zone in self.ignore_zones):
            return False
        if self.detection_zones and not any(
            point_in_polygon(center, zone) for zone in self.detection_zones
        ):
            return False
        return True

    def filter(self, detections: list[Detection]) -> list[Detection]:
        return [
            detection
            for detection in detections
            if detection.confidence >= self.config.confidence
            and detection.label in self.config.object_classes
            and self.allows(detection)
        ]


class NullDetector:
    def detect(self, frame: Any, timestamp: datetime) -> FrameDetections:
        return FrameDetections(timestamp=timestamp, detections=[])


class YoloDetector:
    def __init__(self, model_name: str = "yolov8n.pt") -> None:
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise RuntimeError(
                "Ultralytics is not installed. Install nest-ai-recorder[ai]."
            ) from exc

        self.model = YOLO(model_name)

    def detect(self, frame: Any, timestamp: datetime) -> FrameDetections:
        results = self.model(frame, verbose=False)
        detections: list[Detection] = []
        for result in results:
            names = result.names
            for box in result.boxes:
                left, top, right, bottom = [float(value) for value in box.xyxy[0]]
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                detections.append(
                    Detection(
                        label=str(names[class_id]),
                        confidence=confidence,
                        box=Box(left, top, right, bottom),
                    )
                )
        return FrameDetections(timestamp=timestamp, detections=detections)


class MotionDetector:
    def __init__(self, threshold: float = 25.0, min_score: float = 0.02) -> None:
        self.threshold = threshold
        self.min_score = min_score
        self._previous_gray: Any | None = None

    def score(self, frame: Any) -> float:
        try:
            import cv2
        except ImportError as exc:
            raise RuntimeError("OpenCV is not installed. Install nest-ai-recorder[ai].") from exc

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        if self._previous_gray is None:
            self._previous_gray = gray
            return 0.0

        delta = cv2.absdiff(self._previous_gray, gray)
        self._previous_gray = gray
        changed_pixels = delta > self.threshold
        return float(changed_pixels.sum()) / float(changed_pixels.size)

    def has_motion(self, frame: Any) -> bool:
        return self.score(frame) >= self.min_score

    def score_between(self, first: Any, second: Any) -> float:
        try:
            import cv2
        except ImportError as exc:
            raise RuntimeError("OpenCV is not installed. Install nest-ai-recorder[ai].") from exc

        first_gray = cv2.GaussianBlur(cv2.cvtColor(first, cv2.COLOR_BGR2GRAY), (21, 21), 0)
        second_gray = cv2.GaussianBlur(cv2.cvtColor(second, cv2.COLOR_BGR2GRAY), (21, 21), 0)
        if first_gray.shape != second_gray.shape:
            second_gray = cv2.resize(second_gray, (first_gray.shape[1], first_gray.shape[0]))

        delta = cv2.absdiff(first_gray, second_gray)
        changed_pixels = delta > self.threshold
        return float(changed_pixels.sum()) / float(changed_pixels.size)

    def has_motion_between(self, first: Any, second: Any) -> bool:
        return self.score_between(first, second) >= self.min_score


class IouTracker:
    def __init__(self, iou_threshold: float = 0.35, max_missed: int = 5) -> None:
        self.iou_threshold = iou_threshold
        self.max_missed = max_missed
        self._next_id = 1
        self._tracks: dict[str, tuple[Box, int]] = {}

    def update(self, detections: list[Detection]) -> list[Detection]:
        assigned: set[str] = set()
        tracked: list[Detection] = []

        for detection in detections:
            best_track_id: str | None = None
            best_iou = 0.0
            for track_id, (track_box, _) in self._tracks.items():
                if track_id in assigned:
                    continue
                iou = detection.box.intersection_over_union(track_box)
                if iou > best_iou:
                    best_iou = iou
                    best_track_id = track_id

            if best_track_id is None or best_iou < self.iou_threshold:
                best_track_id = str(self._next_id)
                self._next_id += 1

            assigned.add(best_track_id)
            self._tracks[best_track_id] = (detection.box, 0)
            tracked.append(
                Detection(
                    label=detection.label,
                    confidence=detection.confidence,
                    box=detection.box,
                    track_id=best_track_id,
                )
            )

        for track_id, (box, missed) in list(self._tracks.items()):
            if track_id in assigned:
                continue
            missed += 1
            if missed > self.max_missed:
                del self._tracks[track_id]
            else:
                self._tracks[track_id] = (box, missed)

        return tracked

