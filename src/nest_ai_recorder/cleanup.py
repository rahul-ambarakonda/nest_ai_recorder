from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path


def delete_expired_files(directory: Path, retention_days: int, pattern: str = "*.mp4") -> int:
    if not directory.exists():
        return 0

    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    deleted = 0
    for path in directory.rglob(pattern):
        modified = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
        if modified < cutoff:
            path.unlink()
            deleted += 1
    return deleted

