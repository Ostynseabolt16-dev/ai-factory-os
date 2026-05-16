"""Workflow analytics from local workflow history and task history."""

from __future__ import annotations

from collections import Counter

from ai_factory.analytics.revenue_analytics import revenue_by_batch
from ai_factory.workflows.workflow_engine import get_workflow_history, refresh_workflow_statuses


def workflow_success_rate() -> float:
    workflows = refresh_workflow_statuses()
    if not workflows:
        return 0.0
    completed = len([row for row in workflows if row.get("status") == "completed"])
    return round(completed / len(workflows), 4)


def average_workflow_duration() -> float:
    """Placeholder duration from available workflow metadata; tasks track true durations."""
    workflows = get_workflow_history()
    return 0.0 if not workflows else 0.0


def most_common_failed_stage() -> str:
    workflows = refresh_workflow_statuses()
    failed = [row.get("workflow_type", "") for row in workflows if row.get("status") == "failed"]
    if not failed:
        return "none"
    return Counter(failed).most_common(1)[0][0]


def most_profitable_workflow_type() -> str:
    """Infer from current batch revenue until workflow/product links mature."""
    batch_revenue = revenue_by_batch()
    if not batch_revenue:
        return "none"
    return "batch_pipeline" if batch_revenue[0][1] > 0 else "none"


def workflow_completion_distribution() -> dict[str, int]:
    counts = Counter(row.get("status", "pending") for row in refresh_workflow_statuses())
    return dict(counts)


def bottleneck_stage_detection() -> str:
    distribution = workflow_completion_distribution()
    if distribution.get("failed"):
        return "failed_workflows"
    if distribution.get("running"):
        return "running_workflows"
    if distribution.get("pending"):
        return "pending_workflows"
    return "none"
