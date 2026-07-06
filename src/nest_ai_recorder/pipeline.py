from __future__ import annotations

from datetime import datetime
from pathlib import Path

from nest_ai_recorder.clips import clip_output_path, merge_segments, plan_clip_segments
from nest_ai_recorder.config import AppConfig
from nest_ai_recorder.detection import Detection, IouTracker, ZoneFilter
from nest_ai_recorder.events import DetectionEvent, EventDeduplicator, event_from_detection
from nest_ai_recorder.mqtt import MqttPublisher, event_payload
from nest_ai_recorder.segments import Segment, discover_segments
from nest_ai_recorder.stats import StatsStore


class EventPipeline:
    def __init__(
        self,
        config: AppConfig,
        mqtt: MqttPublisher | None = None,
        stats: StatsStore | None = None,
    ) -> None:
        self.config = config
        self.zone_filter = ZoneFilter(config.detection)
        self.tracker = IouTracker()
        self.deduplicator = EventDeduplicator(config.detection.cooldown_seconds)
        self.mqtt = mqtt
        self.stats = stats

    def prepare_detections(self, detections: list[Detection]) -> list[Detection]:
        return self.tracker.update(self.zone_filter.filter(detections))

    async def handle_detection(
        self,
        detection: Detection,
        timestamp: datetime,
        known_segments: list[Segment] | None = None,
    ) -> Path | None:
        event = event_from_detection(detection, self.config.camera.name, timestamp)
        if not self.deduplicator.should_emit(event):
            return None

        clip_path = await self.create_clip(event, known_segments)
        if self.stats is not None:
            self.stats.stats.record_event(event.event_type, event.timestamp)
            if clip_path is not None:
                self.stats.stats.record_clip(clip_path)
            self.stats.save()

        if self.mqtt is not None:
            self.mqtt.publish(event_payload(event, clip_path, self.config.mqtt.topic_prefix))

        return clip_path

    async def create_clip(
        self,
        event: DetectionEvent,
        known_segments: list[Segment] | None = None,
    ) -> Path | None:
        segments = known_segments or discover_segments(
            self.config.buffer.directory,
            self.config.buffer.segment_seconds,
        )
        segment_paths = plan_clip_segments(
            segments,
            event.timestamp,
            self.config.clips.pre_buffer_seconds,
            self.config.clips.post_buffer_seconds,
        )
        if not segment_paths:
            return None

        output_path = clip_output_path(
            self.config.clips.output_directory,
            event.event_type,
            event.timestamp,
        )
        return await merge_segments(
            segment_paths,
            output_path,
            timeout_seconds=self.config.clips.merge_timeout_seconds,
        )
