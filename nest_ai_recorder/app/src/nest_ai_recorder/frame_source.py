from __future__ import annotations

import asyncio
import logging
import os
import subprocess
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


@dataclass(frozen=True, slots=True)
class SegmentFrames:
    path: Path
    first: Any
    last: Any
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
    def _decode_jpeg(data: bytes) -> Any | None:
        try:
            import cv2
            import numpy as np
        except ImportError as exc:
            raise RuntimeError("OpenCV is not installed. Install nest-ai-recorder[ai].") from exc

        array = np.frombuffer(data, dtype=np.uint8)
        return cv2.imdecode(array, cv2.IMREAD_COLOR)

    @classmethod
    def _ffmpeg_frame(cls, path: Path, from_end: bool = False) -> Any | None:
        command = ["ffmpeg", "-hide_banner", "-loglevel", "error"]
        if from_end:
            command.extend(["-sseof", "-1"])
        command.extend(
            [
                "-i",
                str(path),
                "-frames:v",
                "1",
                "-f",
                "image2pipe",
                "-vcodec",
                "mjpeg",
                "-",
            ]
        )
        result = subprocess.run(command, capture_output=True, check=False)
        if result.returncode != 0 or not result.stdout:
            LOGGER.warning(
                "failed to extract frame from segment",
                extra={
                    "segment": str(path),
                    "from_end": from_end,
                    "stderr": result.stderr.decode("utf-8", errors="replace")[-300:],
                },
            )
            return None
        return cls._decode_jpeg(result.stdout)

    def _read_segment_frames(self, path: Path) -> tuple[Any | None, Any | None]:
        first = self._ffmpeg_frame(path, from_end=False)
        last = self._ffmpeg_frame(path, from_end=True)
        return first, last

    async def frames(self) -> AsyncIterator[VideoFrame]:
        async for segment in self.segment_frames():
            yield VideoFrame(image=segment.last, timestamp=segment.timestamp)

    async def segment_frames(self) -> AsyncIterator[SegmentFrames]:
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

            first, last = await asyncio.to_thread(self._read_segment_frames, target)
            if first is None or last is None:
                await asyncio.sleep(self.interval_seconds)
                continue

            last_segment = target
            LOGGER.debug("sampled frames from segment", extra={"segment": str(target)})
            yield SegmentFrames(
                path=target,
                first=first,
                last=last,
                timestamp=datetime.now(timezone.utc),
            )
            await asyncio.sleep(self.interval_seconds)
