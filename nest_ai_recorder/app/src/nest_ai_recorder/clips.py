from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

from nest_ai_recorder.segments import Segment, select_segments


def clip_output_path(base_directory: Path, event_type: str, event_time: datetime) -> Path:
    month_dir = event_time.strftime("%m-%Y")
    day_dir = event_time.strftime("%d-%m-%Y")
    filename = f"{event_type}_{event_time.strftime('%Y%m%d_%H%M%S')}.mp4"
    return base_directory / month_dir / day_dir / filename


def plan_clip_segments(
    segments: list[Segment],
    event_time: datetime,
    pre_buffer_seconds: int,
    post_buffer_seconds: int,
) -> list[Path]:
    return [
        segment.path
        for segment in select_segments(
            segments,
            event_time,
            pre_buffer_seconds,
            post_buffer_seconds,
        )
    ]


def build_ffmpeg_concat_command(segment_paths: list[Path], output_path: Path) -> list[str]:
    if not segment_paths:
        raise ValueError("at least one segment is required to create a clip")
    return [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "warning",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        "{concat_file}",
        "-c",
        "copy",
        str(output_path),
    ]


async def merge_segments(
    segment_paths: list[Path],
    output_path: Path,
    timeout_seconds: int = 120,
) -> Path:
    if not segment_paths:
        raise ValueError("at least one segment is required to create a clip")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", suffix=".txt", delete=False) as handle:
        concat_file = Path(handle.name)
        for segment_path in segment_paths:
            escaped = str(segment_path).replace("'", "'\\''")
            handle.write(f"file '{escaped}'\n")

    command = [
        part if part != "{concat_file}" else str(concat_file)
        for part in build_ffmpeg_concat_command(segment_paths, output_path)
    ]

    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout_seconds)
        if process.returncode != 0:
            raise RuntimeError(stderr.decode("utf-8", errors="replace"))
    finally:
        concat_file.unlink(missing_ok=True)

    return output_path
