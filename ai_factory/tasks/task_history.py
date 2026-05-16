"""Task execution history and analytics."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

from ai_factory.config import TASK_HISTORY_CSV
from ai_factory.tasks.audit_log import audit_log
from ai_factory.tasks.task_models import now_iso

HISTORY_COLUMNS = [
    "task_id",
    "type",
    "started_at",
    "completed_at",
    "duration_seconds",
    "success",
    "error",
    "output",
]


def _ensure_history(path: Path | None = None) -> Path:
    path = path or TASK_HISTORY_CSV
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as f:
            csv.DictWriter(f, fieldnames=HISTORY_COLUMNS).writeheader()
    return path


def read_task_history(path: Path | None = None) -> list[dict[str, str]]:
    path = _ensure_history(path)
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _write_history(rows: list[dict[str, str]], path: Path | None = None) -> None:
    path = _ensure_history(path)
    with NamedTemporaryFile("w", encoding="utf-8", newline="", delete=False, dir=path.parent) as tmp:
        writer = csv.DictWriter(tmp, fieldnames=HISTORY_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in HISTORY_COLUMNS})
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)


def _duration_seconds(started_at: str, completed_at: str) -> float:
    try:
        start = datetime.fromisoformat(started_at)
        end = datetime.fromisoformat(completed_at)
        return round((end - start).total_seconds(), 3)
    except ValueError:
        return 0.0


def log_task_history(
    task: dict[str, str],
    *,
    success: bool,
    output: dict | str | None = None,
    error: str = "",
    path: Path | None = None,
) -> None:
    """Append one task execution history row."""
    started_at = task.get("started_at") or now_iso()
    completed_at = task.get("completed_at") or now_iso()
    rows = read_task_history(path)
    rows.append(
        {
            "task_id": task.get("id", ""),
            "type": task.get("type", ""),
            "started_at": started_at,
            "completed_at": completed_at,
            "duration_seconds": str(_duration_seconds(started_at, completed_at)),
            "success": str(success),
            "error": error,
            "output": json.dumps(output, sort_keys=True) if isinstance(output, dict) else str(output or ""),
        }
    )
    _write_history(rows, path)
    audit_log(
        f"Logged history task={task.get('id', '')} success={success} error={error or 'none'}",
        event="history",
    )


def average_task_duration(path: Path | None = None) -> float:
    durations = []
    for row in read_task_history(path):
        try:
            durations.append(float(row.get("duration_seconds") or 0))
        except ValueError:
            continue
    if not durations:
        return 0.0
    return round(sum(durations) / len(durations), 3)


def task_success_rate(path: Path | None = None) -> float:
    rows = read_task_history(path)
    if not rows:
        return 0.0
    successes = sum(1 for row in rows if row.get("success") == "True")
    return round(successes / len(rows), 4)


def most_common_failures(path: Path | None = None, *, limit: int = 5) -> list[tuple[str, int]]:
    counts: dict[str, int] = {}
    for row in read_task_history(path):
        error = (row.get("error") or "").strip()
        if error:
            counts[error] = counts.get(error, 0) + 1
    return sorted(counts.items(), key=lambda item: item[1], reverse=True)[:limit]


def most_common_failure_type(path: Path | None = None) -> str:
    """Return the most common failure error, or 'none'."""
    failures = most_common_failures(path, limit=1)
    return failures[0][0] if failures else "none"


def tasks_completed_today(path: Path | None = None) -> int:
    """Count completed history rows for the current local date."""
    today = now_iso().split("T")[0]
    return sum(1 for row in read_task_history(path) if row.get("completed_at", "").startswith(today))


def pending_task_age_seconds(tasks: list[dict[str, str]] | None = None) -> float:
    """Return age in seconds of the oldest pending task from queue rows."""
    if not tasks:
        return 0.0
    ages: list[float] = []
    now = datetime.fromisoformat(now_iso())
    for task in tasks:
        try:
            created = datetime.fromisoformat(task.get("created_at") or now_iso())
        except ValueError:
            continue
        ages.append((now - created).total_seconds())
    return round(max(ages), 3) if ages else 0.0
