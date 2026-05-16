"""Task model constants and helpers for AI Factory OS."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime

ALLOWED_TASK_STATUSES = [
    "pending",
    "queued",
    "running",
    "completed",
    "failed",
    "cancelled",
]

ALLOWED_TASK_TYPES = [
    "niche_research",
    "generate_designs",
    "generate_variants",
    "create_mockups",
    "generate_mockups",
    "generate_listing",
    "review_product",
    "review_products",
    "archive_product",
    "create_variant",
    "upload_products",
    "analytics_refresh",
    "batch_generation",
    "batch_review",
    "batch_mockups",
]

PRIORITY_LEVELS = ["low", "normal", "high", "critical"]
PRIORITY_ORDER = {"critical": 0, "high": 1, "normal": 2, "low": 3}

TASK_COLUMNS = [
    "id",
    "type",
    "status",
    "priority",
    "created_at",
    "started_at",
    "completed_at",
    "payload",
    "result",
    "error",
    "assigned_agent",
    "retry_count",
    "max_retries",
    "last_retry_at",
]


def now_iso() -> str:
    """Return a timestamp without microseconds for CSV readability."""
    return datetime.now().replace(microsecond=0).isoformat()


@dataclass
class Task:
    id: str
    type: str
    status: str
    priority: str
    created_at: str
    started_at: str = ""
    completed_at: str = ""
    payload: str = "{}"
    result: str = ""
    error: str = ""
    assigned_agent: str = ""
    retry_count: str = "0"
    max_retries: str = "3"
    last_retry_at: str = ""

    def to_row(self) -> dict[str, str]:
        """Convert task to a CSV row."""
        return {column: str(asdict(self).get(column, "")) for column in TASK_COLUMNS}


def validate_task_type(task_type: str) -> str:
    task_type = task_type.strip()
    if task_type not in ALLOWED_TASK_TYPES:
        raise ValueError(f"Invalid task type: {task_type}")
    return task_type


def validate_status(status: str) -> str:
    status = status.strip().lower()
    if status not in ALLOWED_TASK_STATUSES:
        raise ValueError(f"Invalid task status: {status}")
    return status


def validate_priority(priority: str) -> str:
    priority = (priority or "normal").strip().lower()
    if priority not in PRIORITY_LEVELS:
        raise ValueError(f"Invalid priority: {priority}")
    return priority
