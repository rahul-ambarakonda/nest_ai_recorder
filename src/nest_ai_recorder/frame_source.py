from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, AsyncIterator


@dataclass(frozen=True, slots=True)
class VideoFrame:
    image: Any
    timestamp: datetime


class RtspFrameSource:
    def __init__(self, rtsp_url: str, interval_seconds: float = 1.0) -> None:
        self.rtsp_url = rtsp_url
        self.interval_seconds = interval_seconds

    async def frames(self) -> AsyncIterator[VideoFrame]:
        try:
            import cv2
        except ImportError as exc:
            raise RuntimeError("OpenCV is not installed. Install nest-ai-recorder[ai].") from exc

        capture = cv2.VideoCapture(self.rtsp_url)
        if not capture.isOpened():
            raise RuntimeError(f"could not open RTSP stream: {self.rtsp_url}")

        try:
            while True:
                ok, frame = await asyncio.to_thread(capture.read)
                if ok:
                    yield VideoFrame(image=frame, timestamp=datetime.now(timezone.utc))
                await asyncio.sleep(self.interval_seconds)
        finally:
            capture.release()
