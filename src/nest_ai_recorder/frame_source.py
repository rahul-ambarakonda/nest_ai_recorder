from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncIterator

from nest_ai_recorder.segments import discover_segments

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class VideoFrame:
    image: Any
    timestamp: datetime


class RtspFrameSource:
    def __init__(
        self,
        rtsp_url: str,
        interval_seconds: float = 1.0,
        rtsp_transport: str = "tcp",
        open_timeout_microseconds: int = 5_000_000,
        read_timeout_microseconds: int = 5_000_000,
        reconnect_delay_seconds: float = 5.0,
    ) -> None:
        self.rtsp_url = rtsp_url
        self.interval_seconds = interval_seconds
        self.rtsp_transport = rtsp_transport
        self.open_timeout_microseconds = open_timeout_microseconds
        self.read_timeout_microseconds = read_timeout_microseconds
        self.reconnect_delay_seconds = reconnect_delay_seconds

    def _capture_options(self) -> str:
        return "|".join(
            [
                f"rtsp_transport;{self.rtsp_transport}",
                f"stimeout;{self.read_timeout_microseconds}",
                f"timeout;{self.open_timeout_microseconds}",
                "fflags;+discardcorrupt",
                "flags;low_delay",
            ]
        )

    async def frames(self) -> AsyncIterator[VideoFrame]:
        try:
            import cv2
        except ImportError as exc:
            raise RuntimeError("OpenCV is not installed. Install nest-ai-recorder[ai].") from exc

        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = self._capture_options()

        while True:
            capture = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
            if not capture.isOpened():
                LOGGER.warning("could not open live stream; retrying")
                capture.release()
                await asyncio.sleep(self.reconnect_delay_seconds)
                continue

            try:
                while True:
                    ok, frame = await asyncio.to_thread(capture.read)
                    if not ok:
                        LOGGER.warning("live stream frame read failed; reconnecting")
                        break
                    yield VideoFrame(image=frame, timestamp=datetime.now(timezone.utc))
                    await asyncio.sleep(self.interval_seconds)
            finally:
                capture.release()

            await asyncio.sleep(self.reconnect_delay_seconds)


class BufferFrameSource:
    """Sample frames from completed recorder segments to avoid a second live stream."""

    def __init__(
        self,
        buffer_directory: Path,
        segment_seconds: int,
        interval_seconds: float = 1.0,
    ) -> None:
        self.buffer_directory = buffer_directory
        self.segment_seconds = segment_seconds
        self.interval_seconds = interval_seconds

    @staticmethod
    def _read_frame(path: Path) -> Any | None:
        try:
            import cv2
        except ImportError as exc:
            raise RuntimeError("OpenCV is not installed. Install nest-ai-recorder[ai].") from exc

        capture = cv2.VideoCapture(str(path))
        if not capture.isOpened():
            capture.release()
            return None

        try:
            frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
            if frame_count > 1:
                capture.set(cv2.CAP_PROP_POS_FRAMES, frame_count - 1)
            ok, frame = capture.read()
            return frame if ok else None
        finally:
            capture.release()

    async def frames(self) -> AsyncIterator[VideoFrame]:
        last_segment: Path | None = None
        while True:
            segments = discover_segments(self.buffer_directory, self.segment_seconds)
            if len(segments) < 2:
                await asyncio.sleep(self.interval_seconds)
                continue

            target = segments[-2].path
            if target == last_segment:
                await asyncio.sleep(self.interval_seconds)
                continue

            frame = await asyncio.to_thread(self._read_frame, target)
            if frame is not None:
                last_segment = target
                yield VideoFrame(image=frame, timestamp=datetime.now(timezone.utc))

            await asyncio.sleep(self.interval_seconds)
