"""Persistent CSV task queue."""

from __future__ import annotations

import csv
import json
import uuid
from pathlib import Path
from tempfile import NamedTemporaryFile

from ai_factory.config import TASK_QUEUE_CSV
from ai_factory.tasks.audit_log import audit_log
from ai_factory.tasks.task_models import (
    PRIORITY_ORDER,
    TASK_COLUMNS,
    Task,
    now_iso,
    validate_priority,
    validate_status,
    validate_task_type,
)

DEFAULT_MAX_RETRIES = 3


def _ensure_queue(path: Path | None = None) -> Path:
    path = path or TASK_QUEUE_CSV
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as f:
            csv.DictWriter(f, fieldnames=TASK_COLUMNS).writeheader()
        return path

    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        existing_columns = reader.fieldnames or []
        rows = list(reader)

    if existing_columns != TASK_COLUMNS:
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=TASK_COLUMNS)
            writer.writeheader()
            for row in rows:
                migrated = {column: row.get(column, "") for column in TASK_COLUMNS}
                migrated["retry_count"] = migrated["retry_count"] or "0"
                migrated["max_retries"] = migrated["max_retries"] or str(DEFAULT_MAX_RETRIES)
                writer.writerow(migrated)
    return path


def _read_tasks(path: Path | None = None) -> list[dict[str, str]]:
    path = _ensure_queue(path)
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _write_tasks(rows: list[dict[str, str]], path: Path | None = None) -> None:
    path = _ensure_queue(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", newline="", delete=False, dir=path.parent) as tmp:
        writer = csv.DictWriter(tmp, fieldnames=TASK_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in TASK_COLUMNS})
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)


def add_task(
    task_type: str,
    *,
    payload: dict | None = None,
    priority: str = "normal",
    assigned_agent: str = "founder_agent",
    status: str = "queued",
    max_retries: int = DEFAULT_MAX_RETRIES,
    path: Path | None = None,
) -> str:
    """Add a persistent task and return its id."""
    try:
        payload_json = json.dumps(payload or {}, sort_keys=True)
    except TypeError as exc:
        raise ValueError(f"Task payload must be JSON-serializable: {exc}") from exc

    task = Task(
        id=str(uuid.uuid4()),
        type=validate_task_type(task_type),
        status=validate_status(status),
        priority=validate_priority(priority),
        created_at=now_iso(),
        payload=payload_json,
        assigned_agent=assigned_agent,
        max_retries=str(max_retries),
    )
    rows = _read_tasks(path)
    rows.append(task.to_row())
    _write_tasks(rows, path)
    audit_log(f"Added task {task.id} type={task.type} priority={task.priority}", event="queue")
    return task.id


def get_next_task(path: Path | None = None) -> dict[str, str] | None:
    """Return highest-priority queued/pending task without mutating queue."""
    candidates = [row for row in _read_tasks(path) if row.get("status") in {"pending", "queued"}]
    if not candidates:
        return None
    return sorted(
        candidates,
        key=lambda row: (PRIORITY_ORDER.get(row.get("priority", "normal"), 2), row.get("created_at", "")),
    )[0]


def update_task_status(
    task_id: str,
    status: str,
    *,
    result: dict | str | None = None,
    error: str = "",
    path: Path | None = None,
) -> dict[str, str]:
    """Update status/result/error timestamps for one task."""
    status = validate_status(status)
    rows = _read_tasks(path)
    for row in rows:
        if row.get("id") == task_id:
            row["status"] = status
            if status == "running":
                row["started_at"] = row.get("started_at") or now_iso()
            if status in {"completed", "failed", "cancelled"}:
                row["completed_at"] = now_iso()
            if result is not None:
                row["result"] = json.dumps(result, sort_keys=True) if isinstance(result, dict) else str(result)
            if error:
                row["error"] = error
            _write_tasks(rows, path)
            audit_log(f"Task {task_id} status -> {status}", event="queue")
            return row
    raise ValueError(f"Task id not found: {task_id}")


def cancel_task(task_id: str, path: Path | None = None) -> dict[str, str]:
    rows = _read_tasks(path)
    for row in rows:
        if row.get("id") == task_id and row.get("status") in {"completed", "cancelled"}:
            raise ValueError(f"Cannot cancel task in status: {row.get('status')}")
    audit_log(f"Cancelled task {task_id}", event="queue")
    return update_task_status(task_id, "cancelled", path=path)


def retry_task(task_id: str, path: Path | None = None) -> dict[str, str]:
    """Reset a failed/cancelled/running task back to queued."""
    rows = _read_tasks(path)
    for row in rows:
        if row.get("id") == task_id:
            retry_count = int(row.get("retry_count") or "0")
            max_retries = int(row.get("max_retries") or str(DEFAULT_MAX_RETRIES))
            if retry_count >= max_retries:
                raise ValueError(f"Task {task_id} has reached max retries ({max_retries}).")
            row["status"] = "queued"
            row["started_at"] = ""
            row["completed_at"] = ""
            row["error"] = ""
            row["retry_count"] = str(retry_count + 1)
            row["last_retry_at"] = now_iso()
            _write_tasks(rows, path)
            audit_log(f"Retried task {task_id} retry_count={row['retry_count']}", event="queue")
            return row
    raise ValueError(f"Task id not found: {task_id}")


def get_pending_tasks(path: Path | None = None) -> list[dict[str, str]]:
    return [row for row in _read_tasks(path) if row.get("status") in {"pending", "queued"}]


def get_running_tasks(path: Path | None = None) -> list[dict[str, str]]:
    return [row for row in _read_tasks(path) if row.get("status") == "running"]


def get_completed_tasks(path: Path | None = None) -> list[dict[str, str]]:
    return [row for row in _read_tasks(path) if row.get("status") == "completed"]


def get_failed_tasks(path: Path | None = None) -> list[dict[str, str]]:
    return [row for row in _read_tasks(path) if row.get("status") == "failed"]


def get_recent_tasks(limit: int = 10, path: Path | None = None) -> list[dict[str, str]]:
    rows = _read_tasks(path)
    return sorted(rows, key=lambda row: row.get("created_at", ""), reverse=True)[:limit]
