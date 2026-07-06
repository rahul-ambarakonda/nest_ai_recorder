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
        self._stop_requested = False

    @property
    def output_pattern(self) -> Path:
        return self.config.buffer.directory / f"{self.config.camera.name}_%Y%m%dT%H%M%SZ.mp4"

    @staticmethod
    def _is_rtsp_url(url: str) -> bool:
        return url.lower().startswith("rtsp://")

    def build_command(self) -> list[str]:
        segment_seconds = str(self.config.buffer.segment_seconds)
        camera = self.config.camera
        command = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "warning",
            "-fflags",
            "+genpts+discardcorrupt+nobuffer",
            "-err_detect",
            "ignore_err",
            "-analyzeduration",
            str(camera.analyze_duration_microseconds),
            "-probesize",
            str(camera.probe_size),
            "-use_wallclock_as_timestamps",
            "1",
        ]

        if self._is_rtsp_url(camera.rtsp_url):
            command.extend(
                [
                    "-rtsp_transport",
                    camera.rtsp_transport,
                    "-rtsp_flags",
                    "prefer_tcp",
                    "-timeout",
                    str(camera.open_timeout_microseconds),
                    "-rw_timeout",
                    str(camera.read_timeout_microseconds),
                ]
            )
        else:
            command.extend(
                [
                    "-reconnect",
                    "1",
                    "-reconnect_streamed",
                    "1",
                    "-reconnect_delay_max",
                    "5",
                ]
            )

        command.extend(["-i", camera.rtsp_url, "-an"])

        if camera.video_codec == "copy":
            command.extend(["-c:v", "copy"])
        else:
            command.extend(
                [
                    "-ec",
                    "guess_mvs+deblock",
                    "-c:v",
                    "libx264",
                    "-preset",
                    camera.video_preset,
                    "-tune",
                    "zerolatency",
                ]
            )

        command.extend(
            [
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
        )
        return command

    async def run(self) -> int:
        last_return_code = 0
        while not self._stop_requested:
            self.config.buffer.directory.mkdir(parents=True, exist_ok=True)
            command = self.build_command()
            LOGGER.info("starting recorder", extra={"command": command})
            self._process = await asyncio.create_subprocess_exec(*command)
            last_return_code = await self._process.wait()
            self._process = None
            if self._stop_requested:
                break
            LOGGER.warning(
                "recorder exited unexpectedly; restarting in 5 seconds",
                extra={"return_code": last_return_code},
            )
            await asyncio.sleep(5)
        return last_return_code

    async def stop(self) -> None:
        self._stop_requested = True
        if self._process is None or self._process.returncode is not None:
            return
        self._process.terminate()
        try:
            await asyncio.wait_for(self._process.wait(), timeout=10)
        except TimeoutError:
            self._process.kill()
            await self._process.wait()
