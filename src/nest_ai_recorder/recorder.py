from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from nest_ai_recorder.config import AppConfig

LOGGER = logging.getLogger(__name__)


class SegmentRecorder:
    """Runs ffmpeg as a long-lived process that writes rotating MP4 segments."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._process: asyncio.subprocess.Process | None = None

    @property
    def output_pattern(self) -> Path:
        return self.config.buffer.directory / f"{self.config.camera.name}_%Y%m%dT%H%M%SZ.mp4"

    def build_command(self) -> list[str]:
        segment_seconds = str(self.config.buffer.segment_seconds)
        return [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "warning",
            "-rtsp_transport",
            "tcp",
            "-i",
            self.config.camera.rtsp_url,
            "-an",
            "-c:v",
            "copy",
            "-f",
            "segment",
            "-segment_time",
            segment_seconds,
            "-strftime",
            "1",
            "-reset_timestamps",
            "1",
            str(self.output_pattern),
        ]

    async def run(self) -> int:
        self.config.buffer.directory.mkdir(parents=True, exist_ok=True)
        command = self.build_command()
        LOGGER.info("starting recorder", extra={"command": command})
        self._process = await asyncio.create_subprocess_exec(*command)
        return await self._process.wait()

    async def stop(self) -> None:
        if self._process is None or self._process.returncode is not None:
            return
        self._process.terminate()
        try:
            await asyncio.wait_for(self._process.wait(), timeout=10)
        except TimeoutError:
            self._process.kill()
            await self._process.wait()

