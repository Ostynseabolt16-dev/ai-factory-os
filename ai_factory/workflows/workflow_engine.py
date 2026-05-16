"""Explicit workflow scheduling engine.

Workflows create task sequences and persist their own history. They never run
tasks directly and never loop in the background.
"""

from __future__ import annotations

import csv
import uuid
from pathlib import Path

from ai_factory.config import WORKFLOW_HISTORY_CSV
from ai_factory.production.batch_manager import create_batch
from ai_factory.tasks.audit_log import audit_log
from ai_factory.tasks.task_models import now_iso
from ai_factory.tasks.task_queue import add_task, get_recent_tasks

WORKFLOW_COLUMNS = [
    "workflow_id",
    "workflow_type",
    "created_at",
    "status",
    "task_count",
    "completed_tasks",
    "failed_tasks",
    "notes",
]

ALLOWED_WORKFLOW_STATUSES = ["pending", "running", "completed", "failed", "cancelled"]


def _ensure_history(path: Path | None = None) -> Path:
    path = path or WORKFLOW_HISTORY_CSV
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as f:
            csv.DictWriter(f, fieldnames=WORKFLOW_COLUMNS).writeheader()
    return path


def get_workflow_history(path: Path | None = None) -> list[dict[str, str]]:
    path = _ensure_history(path)
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _write_history(rows: list[dict[str, str]], path: Path | None = None) -> None:
    path = _ensure_history(path)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=WORKFLOW_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in WORKFLOW_COLUMNS})


def _record_workflow(workflow_id: str, workflow_type: str, task_count: int, notes: str = "") -> None:
    rows = get_workflow_history()
    rows.append(
        {
            "workflow_id": workflow_id,
            "workflow_type": workflow_type,
            "created_at": now_iso(),
            "status": "pending",
            "task_count": str(task_count),
            "completed_tasks": "0",
            "failed_tasks": "0",
            "notes": notes,
        }
    )
    _write_history(rows)


def create_workflow(
    workflow_type: str,
    task_specs: list[dict[str, object]],
    *,
    dry_run: bool = False,
    notes: str = "",
) -> dict[str, object]:
    """Create a workflow and optionally schedule its tasks."""
    workflow_id = str(uuid.uuid4())
    created_task_ids: list[str] = []
    _record_workflow(workflow_id, workflow_type, len(task_specs), notes=f"{notes} dry_run={dry_run}".strip())

    if not dry_run:
        for spec in task_specs:
            payload = dict(spec.get("payload") or {})
            payload["workflow_id"] = workflow_id
            task_id = add_task(
                str(spec["type"]),
                payload=payload,
                priority=str(spec.get("priority") or "normal"),
                assigned_agent="workflow_engine",
            )
            created_task_ids.append(task_id)
        audit_log(f"Workflow {workflow_id} scheduled {len(created_task_ids)} task(s)", event="workflow")
    else:
        audit_log(f"Workflow {workflow_id} dry-run created with {len(task_specs)} planned task(s)", event="workflow")

    return {
        "workflow_id": workflow_id,
        "workflow_type": workflow_type,
        "dry_run": dry_run,
        "planned_tasks": task_specs,
        "created_task_ids": created_task_ids,
    }


def create_design_workflow(
    *,
    niche: str,
    amount: int,
    product_ids: list[str] | None = None,
    steps: list[str] | None = None,
    dry_run: bool = False,
) -> dict[str, object]:
    """Schedule a design pipeline workflow."""
    steps = steps or ["niche_research", "generate_designs", "review_product", "generate_mockups", "generate_listing", "analytics_refresh"]
    product_ids = product_ids or []
    specs: list[dict[str, object]] = []
    if "niche_research" in steps:
        specs.append({"type": "niche_research", "priority": "normal", "payload": {"keywords": [niche]}})
    if "generate_designs" in steps:
        specs.append({"type": "generate_designs", "priority": "normal", "payload": {"niche": niche, "amount": amount}})
    for product_id in product_ids:
        if "review_product" in steps:
            specs.append({"type": "review_product", "priority": "normal", "payload": {"product_id": product_id}})
        if "generate_mockups" in steps:
            specs.append({"type": "generate_mockups", "priority": "high", "payload": {"product_id": product_id}})
        if "generate_listing" in steps:
            specs.append({"type": "generate_listing", "priority": "normal", "payload": {"product_id": product_id}})
    if "analytics_refresh" in steps:
        specs.append({"type": "analytics_refresh", "priority": "low", "payload": {}})
    return create_workflow("design_pipeline", specs, dry_run=dry_run, notes=f"niche={niche} amount={amount}")


def create_batch_workflow(
    *,
    niche: str,
    amount: int,
    steps: list[str] | None = None,
    dry_run: bool = False,
) -> dict[str, object]:
    """Schedule a batch pipeline workflow."""
    steps = steps or ["batch_generation", "batch_review", "batch_mockups"]
    batch_id = "dry-run-batch"
    if not dry_run:
        batch_id = create_batch(niche, amount, notes="Created by workflow_engine")
    specs = []
    if "batch_generation" in steps:
        specs.append({"type": "batch_generation", "priority": "normal", "payload": {"batch_id": batch_id, "niche": niche, "amount": amount}})
    if "batch_review" in steps:
        specs.append({"type": "batch_review", "priority": "normal", "payload": {"batch_id": batch_id}})
    if "batch_mockups" in steps:
        specs.append({"type": "batch_mockups", "priority": "high", "payload": {"batch_id": batch_id}})
    return create_workflow("batch_pipeline", specs, dry_run=dry_run, notes=f"batch_id={batch_id} niche={niche}")


def refresh_workflow_statuses() -> list[dict[str, str]]:
    """Refresh workflow history counts from task queue rows."""
    workflows = get_workflow_history()
    tasks = get_recent_tasks(limit=10000)
    for workflow in workflows:
        workflow_id = workflow["workflow_id"]
        linked = [task for task in tasks if workflow_id in (task.get("payload") or "")]
        completed = len([task for task in linked if task.get("status") == "completed"])
        failed = len([task for task in linked if task.get("status") == "failed"])
        task_count = int(workflow.get("task_count") or 0)
        workflow["completed_tasks"] = str(completed)
        workflow["failed_tasks"] = str(failed)
        if failed:
            workflow["status"] = "failed"
        elif task_count and completed >= task_count:
            workflow["status"] = "completed"
        elif linked:
            workflow["status"] = "running"
    _write_history(workflows)
    return workflows
