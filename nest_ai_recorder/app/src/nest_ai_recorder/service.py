from __future__ import annotations

import asyncio
import contextlib
import logging
from datetime import datetime, timezone
from typing import Any, Protocol

from nest_ai_recorder.config import AppConfig
from nest_ai_recorder.dashboard import DashboardServer
from nest_ai_recorder.detection import Detection, MotionDetector, NullDetector, ObjectDetector, YoloDetector
from nest_ai_recorder.frame_source import BufferFrameSource, RtspFrameSource, SegmentFrames
from nest_ai_recorder.geometry import Box
from nest_ai_recorder.mqtt import MqttPublisher
from nest_ai_recorder.pipeline import EventPipeline
from nest_ai_recorder.recorder import SegmentRecorder
from nest_ai_recorder.stats import StatsStore

LOGGER = logging.getLogger(__name__)


class FrameSource(Protocol):
    def frames(self) -> Any:
        ...


class RecorderService:
    def __init__(self, config: AppConfig, detector: ObjectDetector | None = None) -> None:
        self.config = config
        self._use_motion_only = False
        self.recorder = SegmentRecorder(config)
        self.detector = detector or self._build_detector()
        self.frame_source = self._build_frame_source()
        self.motion = MotionDetector(
            threshold=config.detection.motion_threshold,
            min_score=config.detection.motion_min_score,
        )
        self.mqtt = MqttPublisher(config.mqtt)
        self.stats = StatsStore(config.dashboard.stats_path)
        self.pipeline = EventPipeline(config, mqtt=self.mqtt, stats=self.stats)
        self.dashboard = (
            DashboardServer(config.dashboard.stats_path, config.dashboard.host, config.dashboard.port)
            if config.dashboard.enabled
            else None
        )
        self._detection_task: asyncio.Task[None] | None = None

    def _build_frame_source(self) -> FrameSource:
        detection = self.config.detection
        if detection.frame_source == "buffer":
            LOGGER.info(
                "using buffer-based motion detection",
                extra={"directory": str(self.config.buffer.directory)},
            )
            return BufferFrameSource(
                self.config.buffer.directory,
                self.config.buffer.segment_seconds,
                interval_seconds=detection.frame_interval_seconds,
            )

        LOGGER.info(
            "using live stream for motion detection",
            extra={"url": self.config.camera.rtsp_url},
        )
        return RtspFrameSource(
            self.config.camera.rtsp_url,
            interval_seconds=detection.frame_interval_seconds,
            rtsp_transport=self.config.camera.rtsp_transport,
            open_timeout_microseconds=self.config.camera.open_timeout_microseconds,
            read_timeout_microseconds=self.config.camera.read_timeout_microseconds,
            reconnect_delay_seconds=detection.reconnect_delay_seconds,
        )

    def _build_detector(self) -> ObjectDetector:
        if not self.config.detection.enabled:
            return NullDetector()
        try:
            return YoloDetector(self.config.detection.model)
        except RuntimeError as exc:
            LOGGER.warning(
                "YOLO unavailable, falling back to motion-only detection: %s",
                exc,
            )
            self._use_motion_only = True
            return NullDetector()

    async def run(self) -> int:
        self.mqtt.connect()
        if self.dashboard is not None:
            self.stats.save()
            self.dashboard.start()
            LOGGER.info(
                "dashboard started",
                extra={"host": self.config.dashboard.host, "port": self.config.dashboard.port},
            )

        if self.config.detection.enabled:
            self._detection_task = asyncio.create_task(self.run_detection_loop())

        try:
            return await self.recorder.run()
        finally:
            await self.stop()

    async def run_detection_loop(self) -> None:
        if isinstance(self.frame_source, BufferFrameSource):
            async for segment in self.frame_source.segment_frames():
                await self.process_segment_frames(segment)
            return

        async for frame in self.frame_source.frames():
            await self.process_frame(frame.image, frame.timestamp)

    async def process_segment_frames(self, segment: SegmentFrames) -> None:
        timestamp = segment.timestamp
        if self._use_motion_only:
            segment_score = self.motion.score_between(segment.first, segment.last)
            if segment_score >= self.config.detection.motion_min_score:
                LOGGER.info(
                    "motion detected in segment",
                    extra={"score": segment_score, "segment": str(segment.path)},
                )
                await self.pipeline.handle_detection(
                    Detection(
                        label="motion",
                        confidence=min(1.0, segment_score * 5),
                        box=Box(0.0, 0.0, 1.0, 1.0),
                    ),
                    timestamp,
                )
                return

        await self.process_frame(segment.last, timestamp)

    async def stop(self) -> None:
        if self._detection_task is not None:
            self._detection_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._detection_task
            self._detection_task = None
        await self.recorder.stop()
        self.mqtt.close()
        if self.dashboard is not None:
            self.dashboard.stop()

    async def process_frame(self, frame: Any, timestamp: datetime | None = None) -> None:
        timestamp = timestamp or datetime.now(timezone.utc)
        frame_detections = self.detector.detect(frame, timestamp)
        filtered = self.pipeline.prepare_detections(frame_detections.detections)
        if filtered:
            for detection in filtered:
                await self.pipeline.handle_detection(detection, timestamp)
            return

        if self._use_motion_only and self.motion.has_motion(frame):
            score = self.motion.score(frame)
            LOGGER.info("motion detected", extra={"score": score})
            motion_detection = Detection(
                label="motion",
                confidence=min(1.0, score * 5),
                box=Box(0.0, 0.0, 1.0, 1.0),
            )
            await self.pipeline.handle_detection(motion_detection, timestamp)
