"""Safe explicit task execution for AI Factory OS."""

from __future__ import annotations

import json
from pathlib import Path

from ai_factory.analytics.product_analytics import (
    calculate_average_quality,
    calculate_conversion_rate,
    calculate_top_performing_niches,
    estimate_total_revenue,
)
from ai_factory.bulk_generator import generate_bulk_designs
from ai_factory.mockups import generate_product_mockups
from ai_factory.pipeline.product_pipeline import archive_product, review_product
from ai_factory.products.listing_generator import generate_description, generate_tags, generate_title
from ai_factory.products.product_manager import (
    get_recent_products,
    mark_product_uploaded,
    read_products,
    update_product_status,
    write_products,
)
from ai_factory.research.niche_research import save_niche_report
from ai_factory.tasks.audit_log import audit_log
from ai_factory.tasks.task_history import log_task_history
from ai_factory.tasks.task_queue import get_next_task, update_task_status
from ai_factory.variants.variant_generator import (
    create_color_variant,
    create_style_variant,
    create_text_variant,
)
from ai_factory.production.batch_manager import get_batch_products, summarize_batch


def _payload(task: dict[str, str]) -> dict:
    raw = task.get("payload") or "{}"
    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("Task payload must be a JSON object.")
        return data
    except json.JSONDecodeError:
        raise ValueError("Task payload is malformed JSON.")


def _dry_result(task_type: str, payload: dict) -> dict:
    return {
        "dry_run": True,
        "task_type": task_type,
        "payload": payload,
        "message": "Simulated task. No paid APIs, uploads, or generation were run.",
    }


def _run_niche_research(payload: dict, dry_run: bool) -> dict:
    keywords = payload.get("keywords") or ["nurse humor", "teacher gifts", "retro anxiety"]
    if dry_run:
        return _dry_result("niche_research", {"keywords": keywords})
    reports = save_niche_report(list(keywords))
    return {"report_count": len(reports), "top_keyword": reports[0]["keyword"] if reports else ""}


def _run_generate_designs(payload: dict, dry_run: bool) -> dict:
    niche = str(payload.get("niche") or "").strip()
    amount = int(payload.get("amount") or 1)
    batch_id = str(payload.get("batch_id") or "").strip()
    if dry_run:
        return _dry_result("generate_designs", {"niche": niche, "amount": amount, "batch_id": batch_id})
    if not niche:
        raise ValueError("generate_designs requires payload.niche")
    paths = generate_bulk_designs(niche, amount, batch_id=batch_id)
    return {"generated": len(paths), "paths": [str(path) for path in paths]}


def _run_batch_generation(payload: dict, dry_run: bool) -> dict:
    return _run_generate_designs(payload, dry_run)


def _run_generate_variants(payload: dict, dry_run: bool) -> dict:
    niche = str(payload.get("niche") or payload.get("base_niche") or "").strip()
    amount = int(payload.get("amount") or 3)
    if dry_run:
        return _dry_result("generate_variants", {"niche": niche, "amount": amount})
    if not niche:
        raise ValueError("generate_variants requires payload.niche")
    paths = generate_bulk_designs(f"{niche} variant", amount)
    return {"generated": len(paths), "paths": [str(path) for path in paths]}


def _run_create_mockups(payload: dict, dry_run: bool) -> dict:
    product_id = str(payload.get("product_id") or "").strip()
    filename = str(payload.get("filename") or "").strip()
    if dry_run:
        return _dry_result("create_mockups", {"product_id": product_id, "filename": filename})
    if not filename and product_id:
        products = [row for row in read_products() if row.get("id") == product_id]
        if products:
            filename = products[0].get("filename") or products[0].get("image_path") or ""
    if not filename:
        raise ValueError("create_mockups requires product_id or filename")
    outputs = generate_product_mockups(int(product_id or 0), Path(filename))
    output_paths = [str(path) for path in outputs]
    if product_id:
        rows = read_products()
        for row in rows:
            if row.get("id") == product_id:
                row["mockup_paths"] = "|".join(output_paths)
                write_products(rows)
                break
    return {"mockups": output_paths}


def _run_generate_mockups(payload: dict, dry_run: bool) -> dict:
    return _run_create_mockups(payload, dry_run)


def _run_generate_listing(payload: dict, dry_run: bool) -> dict:
    product_id = str(payload.get("product_id") or "").strip()
    if dry_run:
        return _dry_result("generate_listing", {"product_id": product_id})
    if not product_id:
        raise ValueError("generate_listing requires payload.product_id")
    rows = read_products()
    for row in rows:
        if row.get("id") == product_id:
            row["title"] = row.get("title") or generate_title(row)
            row["tags"] = row.get("tags") or generate_tags(row)
            row["description"] = row.get("description") or generate_description(row)
            write_products(rows)
            return {"product_id": product_id, "title": row["title"]}
    raise ValueError(f"Product id not found: {product_id}")


def _run_review_products(payload: dict, dry_run: bool) -> dict:
    product_ids = [str(pid) for pid in payload.get("product_ids", [])]
    if dry_run:
        return _dry_result("review_products", {"product_ids": product_ids})
    updated = []
    for product_id in product_ids:
        update_product_status(product_id, "reviewed")
        updated.append(product_id)
    return {"reviewed": updated}


def _run_review_product(payload: dict, dry_run: bool) -> dict:
    product_id = str(payload.get("product_id") or "").strip()
    if dry_run:
        return _dry_result("review_product", {"product_id": product_id})
    if not product_id:
        raise ValueError("review_product requires payload.product_id")
    return review_product(product_id)  # type: ignore[return-value]


def _run_batch_review(payload: dict, dry_run: bool) -> dict:
    batch_id = str(payload.get("batch_id") or "").strip()
    products = get_batch_products(batch_id) if batch_id else []
    if dry_run:
        return _dry_result("batch_review", {"batch_id": batch_id, "product_count": len(products)})
    reviewed = []
    for product in products:
        reviewed.append(review_product(product["id"]))
    return {"batch_id": batch_id, "reviewed": reviewed}


def _run_archive_product(payload: dict, dry_run: bool) -> dict:
    product_id = str(payload.get("product_id") or "").strip()
    if dry_run:
        return _dry_result("archive_product", {"product_id": product_id})
    if not product_id:
        raise ValueError("archive_product requires payload.product_id")
    return archive_product(product_id)


def _run_create_variant(payload: dict, dry_run: bool) -> dict:
    product_id = str(payload.get("product_id") or "").strip()
    variant_type = str(payload.get("variant_type") or "style").strip().lower()
    if dry_run:
        return _dry_result("create_variant", {"product_id": product_id, "variant_type": variant_type})
    if not product_id:
        raise ValueError("create_variant requires payload.product_id")
    if variant_type == "color":
        variant_id = create_color_variant(product_id)
    elif variant_type == "text":
        variant_id = create_text_variant(product_id)
    else:
        variant_id = create_style_variant(product_id)
    return {"variant_id": variant_id, "parent_product_id": product_id, "variant_type": variant_type}


def _run_batch_mockups(payload: dict, dry_run: bool) -> dict:
    batch_id = str(payload.get("batch_id") or "").strip()
    products = get_batch_products(batch_id) if batch_id else []
    if dry_run:
        return _dry_result("batch_mockups", {"batch_id": batch_id, "product_count": len(products)})
    results = []
    for product in products:
        results.append(_run_generate_mockups({"product_id": product["id"], "filename": product.get("filename", "")}, False))
    summarize_batch(batch_id)
    return {"batch_id": batch_id, "mockup_results": results}


def _run_upload_products(payload: dict, dry_run: bool) -> dict:
    product_ids = [str(pid) for pid in payload.get("product_ids", [])]
    if dry_run:
        return _dry_result("upload_products", {"product_ids": product_ids})
    updated = []
    for product_id in product_ids:
        mark_product_uploaded(product_id)
        updated.append(product_id)
    return {"locally_marked_uploaded": updated, "note": "No external upload API was called."}


def _run_analytics_refresh(payload: dict, dry_run: bool) -> dict:
    if dry_run:
        return _dry_result("analytics_refresh", payload)
    return {
        "conversion_rate": calculate_conversion_rate(),
        "average_quality": calculate_average_quality(),
        "total_revenue": estimate_total_revenue(),
        "top_performing_niches": calculate_top_performing_niches(),
        "recent_products": [row.get("id") for row in get_recent_products(limit=5)],
    }


TASK_ROUTES = {
    "niche_research": _run_niche_research,
    "generate_designs": _run_generate_designs,
    "batch_generation": _run_batch_generation,
    "generate_variants": _run_generate_variants,
    "create_mockups": _run_create_mockups,
    "generate_mockups": _run_generate_mockups,
    "generate_listing": _run_generate_listing,
    "review_product": _run_review_product,
    "review_products": _run_review_products,
    "batch_review": _run_batch_review,
    "archive_product": _run_archive_product,
    "create_variant": _run_create_variant,
    "batch_mockups": _run_batch_mockups,
    "upload_products": _run_upload_products,
    "analytics_refresh": _run_analytics_refresh,
}


def execute_task(task: dict[str, str], *, dry_run: bool = False) -> dict:
    """Execute one task safely and persist queue/history outcome."""
    task_id = task["id"]
    task_type = task["type"]
    running_task = update_task_status(task_id, "running")
    audit_log(f"Starting task {task_id} type={task_type} dry_run={dry_run}", event="runner")

    try:
        payload = _payload(task)
        handler = TASK_ROUTES[task_type]
        result = handler(payload, dry_run)
    except Exception as exc:
        failed_task = update_task_status(task_id, "failed", error=str(exc))
        log_task_history(failed_task, success=False, error=str(exc), output={})
        audit_log(f"Task {task_id} failed: {exc}", event="runner")
        return {"success": False, "task_id": task_id, "error": str(exc)}

    completed_task = update_task_status(task_id, "completed", result=result)
    if running_task.get("started_at") and not completed_task.get("started_at"):
        completed_task["started_at"] = running_task["started_at"]
    log_task_history(completed_task, success=True, output=result)
    audit_log(f"Task {task_id} completed", event="runner")
    return {"success": True, "task_id": task_id, "result": result}


def run_next_task(*, dry_run: bool = False) -> dict:
    """Run the highest-priority queued task once. No loop/daemon."""
    task = get_next_task()
    if not task:
        return {"success": True, "message": "No queued tasks."}
    return execute_task(task, dry_run=dry_run)
