from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, AsyncIterator

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
                LOGGER.warning("could not open RTSP stream; retrying")
                capture.release()
                await asyncio.sleep(self.reconnect_delay_seconds)
                continue

            try:
                while True:
                    ok, frame = await asyncio.to_thread(capture.read)
                    if not ok:
                        LOGGER.warning("RTSP frame read failed; reconnecting")
                        break
                    yield VideoFrame(image=frame, timestamp=datetime.now(timezone.utc))
                    await asyncio.sleep(self.interval_seconds)
            finally:
                capture.release()

            await asyncio.sleep(self.reconnect_delay_seconds)
