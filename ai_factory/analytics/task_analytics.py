"""Task analytics from local queue/history CSV files."""

from __future__ import annotations

from ai_factory.tasks.task_history import (
    average_task_duration,
    most_common_failure_type,
    pending_task_age_seconds,
    task_success_rate,
    tasks_completed_today,
)
from ai_factory.tasks.task_queue import get_pending_tasks


def calculate_task_success_rate() -> float:
    """Return task success rate from task_history.csv."""
    return task_success_rate()


def calculate_average_task_duration() -> float:
    """Return average task execution duration in seconds."""
    return average_task_duration()


def calculate_most_common_failure_type() -> str:
    """Return most common failure error string."""
    return most_common_failure_type()


def calculate_tasks_completed_today() -> int:
    """Return number of task history rows completed today."""
    return tasks_completed_today()


def calculate_pending_task_age() -> float:
    """Return age in seconds of oldest pending/queued task."""
    return pending_task_age_seconds(get_pending_tasks())
