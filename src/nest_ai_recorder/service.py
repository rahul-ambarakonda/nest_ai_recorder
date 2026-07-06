from __future__ import annotations

import asyncio
import contextlib
import logging
from datetime import datetime, timezone
from typing import Any

from nest_ai_recorder.config import AppConfig
from nest_ai_recorder.dashboard import DashboardServer
from nest_ai_recorder.detection import Detection, MotionDetector, NullDetector, ObjectDetector, YoloDetector
from nest_ai_recorder.frame_source import RtspFrameSource
from nest_ai_recorder.geometry import Box
from nest_ai_recorder.mqtt import MqttPublisher
from nest_ai_recorder.pipeline import EventPipeline
from nest_ai_recorder.recorder import SegmentRecorder
from nest_ai_recorder.stats import StatsStore

LOGGER = logging.getLogger(__name__)


class RecorderService:
    def __init__(self, config: AppConfig, detector: ObjectDetector | None = None) -> None:
        self.config = config
        self._use_motion_only = False
        self.recorder = SegmentRecorder(config)
        self.detector = detector or self._build_detector()
        self.frame_source = RtspFrameSource(
            config.camera.rtsp_url,
            interval_seconds=config.detection.frame_interval_seconds,
        )
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
        async for frame in self.frame_source.frames():
            await self.process_frame(frame.image, frame.timestamp)

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
            LOGGER.debug("motion detected", extra={"score": score})
            motion_detection = Detection(
                label="motion",
                confidence=min(1.0, score * 5),
                box=Box(0.0, 0.0, 1.0, 1.0),
            )
            await self.pipeline.handle_detection(motion_detection, timestamp)
