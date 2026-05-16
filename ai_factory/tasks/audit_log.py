"""Append-only local audit log for task and queue events."""

from __future__ import annotations

from pathlib import Path

from ai_factory.config import PROJECT_ROOT
from ai_factory.tasks.task_models import now_iso

LOG_DIR = PROJECT_ROOT / "logs"
SYSTEM_LOG = LOG_DIR / "system.log"


def audit_log(message: str, *, event: str = "system") -> None:
    """Append a timestamped local log line. Never raises into business flow."""
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with SYSTEM_LOG.open("a", encoding="utf-8") as f:
            f.write(f"{now_iso()} [{event}] {message}\n")
    except OSError:
        # Logging should never break task execution or queue updates.
        return
