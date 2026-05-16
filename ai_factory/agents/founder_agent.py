"""Founder Agent for AI Factory OS.

The Founder Agent should make business-level decisions and delegate execution
to specialist modules. For now, its first delegation is bulk design generation.
"""

from __future__ import annotations

from collections import Counter

from ai_factory.analytics.product_analytics import (
    calculate_average_quality,
    estimate_total_revenue,
)
from ai_factory.analytics.revenue_analytics import revenue_by_batch, revenue_by_niche
from ai_factory.products.product_manager import (
    ALLOWED_STATUSES,
    DEFAULT_STATUS,
    get_recent_products,
    get_top_niches,
    read_products,
)
from ai_factory.production.batch_manager import create_batch, get_batch_products
from ai_factory.quality.duplicate_detector import generate_duplicate_report
from ai_factory.research.niche_research import save_niche_report
from ai_factory.tasks.task_history import (
    average_task_duration,
    most_common_failure_type,
    most_common_failures,
    pending_task_age_seconds,
    task_success_rate,
    tasks_completed_today,
)
from ai_factory.tasks.task_queue import (
    add_task,
    get_completed_tasks,
    get_failed_tasks,
    get_next_task,
    get_pending_tasks,
    get_recent_tasks,
    get_running_tasks,
)


def get_founder_metrics() -> dict[str, int]:
    """Return simple business metrics from products.csv."""
    rows = read_products()
    niches = {
        (row.get("niche") or "").strip().lower()
        for row in rows
        if (row.get("niche") or "").strip()
    }
    drafts = [
        row
        for row in rows
        if (row.get("status") or "").strip().lower() == DEFAULT_STATUS
    ]

    return {
        "total_products": len(rows),
        "drafts": len(drafts),
        "niches": len(niches),
    }


def recommend_next_action(metrics: dict[str, int] | None = None) -> str:
    """Make one simple founder recommendation based on local CSV counts."""
    metrics = metrics or get_founder_metrics()

    if metrics["total_products"] == 0:
        return "Generate 3-5 draft designs in one niche before building more automation."
    if metrics["drafts"] >= 10:
        return "Review drafts and manually publish the best 1-2 products before generating more."
    if metrics["niches"] < 3:
        return "Test another niche with a small batch so you can compare product angles."
    return "Check which drafts have the strongest mockups and move the best ones toward Etsy/Printify."


def _status_counts(rows: list[dict[str, str]]) -> dict[str, int]:
    """Count products by allowed lifecycle status."""
    counts = {status: 0 for status in ALLOWED_STATUSES}
    for row in rows:
        status = (row.get("status") or DEFAULT_STATUS).strip().lower()
        if status in counts:
            counts[status] += 1
        else:
            counts[DEFAULT_STATUS] += 1
    return counts


def _newest_row(rows: list[dict[str, str]]) -> dict[str, str] | None:
    """Return the row with the highest numeric id, falling back to last row."""
    if not rows:
        return None

    def row_id(row: dict[str, str]) -> int:
        raw = (row.get("id") or "").strip()
        return int(raw) if raw.isdigit() else 0

    return max(rows, key=row_id)


def _quality_scores(rows: list[dict[str, str]]) -> list[int]:
    """Return numeric quality scores from products.csv rows."""
    scores: list[int] = []
    for row in rows:
        raw = (row.get("quality_score") or "").strip()
        if raw.isdigit():
            scores.append(int(raw))
    return scores


def _score_value(row: dict[str, str]) -> int:
    """Parse quality_score safely for business recommendations."""
    try:
        return int(float((row.get("quality_score") or "0").strip() or 0))
    except ValueError:
        return 0


def _quality_distribution(rows: list[dict[str, str]]) -> dict[str, int]:
    distribution = {"low": 0, "medium": 0, "high": 0}
    for row in rows:
        score = _score_value(row)
        if score >= 3:
            distribution["high"] += 1
        elif score >= 1:
            distribution["medium"] += 1
        else:
            distribution["low"] += 1
    return distribution


def founder_dashboard() -> dict[str, str | int | float]:
    """
    Print a clean business report from local products.csv data.

    This is read-only: no uploads, no API calls, no generation.
    """
    rows = read_products()
    counts = _status_counts(rows)
    top_niches = get_top_niches(limit=3)
    top_niche = top_niches[0][0] if top_niches else "none yet"

    newest = _newest_row(rows)
    newest_product = "none yet"
    if newest:
        newest_product = (
            (newest.get("filename") or "").strip()
            or (newest.get("image_path") or "").strip()
            or "unknown"
        )

    average_quality_score = calculate_average_quality()
    total_revenue = estimate_total_revenue()
    revenue_niches = revenue_by_niche()
    batch_revenue = revenue_by_batch()
    duplicates = generate_duplicate_report()
    reviewed_count = counts["reviewed"]
    upload_ready_count = counts["upload_ready"]
    top_batch = batch_revenue[0] if batch_revenue else ("none", 0)
    worst_batch = batch_revenue[-1] if batch_revenue else ("none", 0)

    report = {
        "total_products": len(rows),
        "drafts": counts["draft"],
        "reviewed_products": reviewed_count,
        "upload_ready_products": upload_ready_count,
        "top_niche": top_niche,
        "newest_product": newest_product,
        "average_quality_score": average_quality_score,
        "uploaded_count": counts["uploaded"],
        "listed_count": counts["listed"],
        "sold_count": counts["sold"],
        "estimated_revenue": total_revenue,
        "revenue_per_niche": revenue_niches,
        "top_batch": top_batch,
        "worst_batch": worst_batch,
        "duplicate_count": len(duplicates),
        "quality_distribution": _quality_distribution(rows),
        "recommended_action": business_recommendations(rows)[0],
    }

    print("\n=== AI FACTORY REPORT ===\n")
    print(f"Total Products: {report['total_products']}")
    print(f"Reviewed Products: {report['reviewed_products']}")
    print(f"Upload-Ready Products: {report['upload_ready_products']}")
    print(f"Drafts: {report['drafts']}")
    print(f"Top Niche: {report['top_niche']}")
    print(f"Newest Product: {report['newest_product']}")
    print(f"Average Quality Score: {report['average_quality_score']}")
    print(f"Uploaded: {report['uploaded_count']}")
    print(f"Listed: {report['listed_count']}")
    print(f"Sold: {report['sold_count']}")
    print(f"Estimated Revenue: ${report['estimated_revenue']}")
    print(f"Revenue Per Niche: {report['revenue_per_niche']}")
    print(f"Top Batch: {report['top_batch']}")
    print(f"Worst Batch: {report['worst_batch']}")
    print(f"Duplicate Count: {report['duplicate_count']}")
    print(f"Quality Distribution: {report['quality_distribution']}")
    print("\nRECOMMENDED ACTION:")
    print(report["recommended_action"])

    return report


def business_recommendations(rows: list[dict[str, str]] | None = None) -> list[str]:
    """Recommend next actions from actual inventory state."""
    rows = rows or read_products()
    counts = _status_counts(rows)
    recommendations: list[str] = []

    upload_ready = counts["upload_ready"]
    reviewed = counts["reviewed"]
    mockup_ready = counts["mockup_ready"]
    high_quality_no_mockups = [
        row
        for row in rows
        if _score_value(row) >= 2
        and not (row.get("mockup_paths") or "").strip()
        and row.get("status") in {"draft", "reviewed"}
    ]
    low_quality_drafts = [
        row
        for row in rows
        if row.get("status") == "draft"
        and _score_value(row) == 0
    ]
    top_niches = get_top_niches(limit=1)

    if upload_ready:
        recommendations.append("Upload reviewed products that are already upload_ready.")
    if reviewed or mockup_ready:
        recommendations.append("Prepare listings and move strong reviewed products to upload_ready.")
    if high_quality_no_mockups:
        recommendations.append("Create mockups for high scoring products.")
    if top_niches and counts["sold"] > 0:
        recommendations.append(f"Generate more products for winning niche: {top_niches[0][0]}.")
    if low_quality_drafts:
        recommendations.append("Archive low quality draft products that are not worth reviewing.")
    if not recommendations:
        recommendations.append("Review newest draft products and prepare the best ones for manual upload.")

    return recommendations


def task_recommendations() -> list[str]:
    """Recommend orchestration tasks from inventory and queue state."""
    rows = read_products()
    pending = get_pending_tasks()
    recommendations: list[str] = []
    counts = _status_counts(rows)
    top_niches = get_top_niches(limit=1)

    if counts["upload_ready"]:
        recommendations.append("Schedule high-priority upload_products tasks for upload_ready products.")
    if counts["reviewed"]:
        recommendations.append("Schedule generate_listing tasks for reviewed products without listing copy.")
    if any(_score_value(row) >= 2 and not row.get("mockup_paths") for row in rows):
        recommendations.append("Schedule create_mockups tasks for high scoring products.")
    if top_niches:
        recommendations.append(f"Schedule generate_variants for top niche: {top_niches[0][0]}.")
    if not any(task.get("type") == "analytics_refresh" for task in pending):
        recommendations.append("Schedule a low-priority analytics_refresh task.")
    if not recommendations:
        recommendations.append("Inspect recent task results and review newest draft products.")
    return recommendations


def generate_founder_recommendations() -> list[dict[str, object]]:
    """Data-driven suggested actions/tasks; never executes anything."""
    rows = read_products()
    pending = get_pending_tasks()
    counts = _status_counts(rows)
    top_niches = get_top_niches(limit=1)
    recommendations: list[dict[str, object]] = []

    stale_drafts = [row for row in rows if row.get("status") == "draft"]
    missing_listings = [
        row
        for row in rows
        if row.get("status") in {"draft", "reviewed"}
        and (not row.get("title") or not row.get("tags") or not row.get("description"))
    ]
    no_mockups = [
        row
        for row in rows
        if row.get("status") in {"draft", "reviewed", "upload_ready"}
        and not (row.get("mockup_paths") or "").strip()
    ]

    if stale_drafts:
        recommendations.append(
            {
                "category": "stale inventory",
                "action": "Review draft products.",
                "task_type": "review_product",
                "payload": {"product_id": stale_drafts[0].get("id")},
                "priority": "normal",
            }
        )
    if missing_listings:
        recommendations.append(
            {
                "category": "highest potential",
                "action": "Create listings for products missing SEO copy.",
                "task_type": "generate_listing",
                "payload": {"product_id": missing_listings[0].get("id")},
                "priority": "normal",
            }
        )
    if no_mockups:
        recommendations.append(
            {
                "category": "high quality not uploaded",
                "action": "Generate mockups for products without mockups.",
                "task_type": "generate_mockups",
                "payload": {"product_id": no_mockups[0].get("id")},
                "priority": "high",
            }
        )
    if top_niches:
        recommendations.append(
            {
                "category": "successful niche expansion candidates",
                "action": f"Generate variants for top niche: {top_niches[0][0]}.",
                "task_type": "create_variant",
                "payload": {"product_id": rows[0].get("id") if rows else "", "variant_type": "style"},
                "priority": "normal",
            }
        )
    if counts["upload_ready"]:
        ready = [row for row in rows if row.get("status") == "upload_ready"]
        recommendations.append(
            {
                "category": "high quality not uploaded",
                "action": "Upload-ready products need manual upload review.",
                "task_type": "upload_products",
                "payload": {"product_ids": [row.get("id") for row in ready[:5]]},
                "priority": "high",
            }
        )
    if len(get_failed_tasks()) >= 3:
        recommendations.append(
            {
                "category": "system reliability",
                "action": "Investigate excessive failed tasks before scheduling more work.",
                "task_type": "analytics_refresh",
                "payload": {},
                "priority": "critical",
            }
        )
    if not any(task.get("type") == "analytics_refresh" for task in pending):
        recommendations.append(
            {
                "category": "throughput visibility",
                "action": "Refresh local analytics.",
                "task_type": "analytics_refresh",
                "payload": {},
                "priority": "low",
            }
        )
    if not recommendations:
        recommendations.append(
            {
                "category": "operations",
                "action": "Inspect recent task results and review newest draft products.",
                "task_type": "analytics_refresh",
                "payload": {},
                "priority": "low",
            }
        )
    return recommendations


def founder_inventory_report() -> dict[str, object]:
    """Print a fuller lifecycle inventory report for the Founder Agent."""
    rows = read_products()
    counts = _status_counts(rows)
    recent = get_recent_products(limit=5)
    top_niches = get_top_niches(limit=5)
    recommendations = business_recommendations(rows)

    report = {
        "total_products": len(rows),
        "products_by_status": counts,
        "top_niches": top_niches,
        "average_quality_score": calculate_average_quality(),
        "uploaded_count": counts["uploaded"],
        "listed_count": counts["listed"],
        "sold_count": counts["sold"],
        "estimated_revenue": estimate_total_revenue(),
        "newest_products": recent,
        "recommendations": recommendations,
    }

    print("\n=== FOUNDER INVENTORY REPORT ===\n")
    print(f"Total Products: {report['total_products']}")
    print("Products by Status:")
    for status in ALLOWED_STATUSES:
        print(f"  {status}: {counts[status]}")
    print(f"Average Quality Score: {report['average_quality_score']}")
    print(f"Estimated Revenue: ${report['estimated_revenue']}")
    print("\nTop Niches:")
    if top_niches:
        for niche, count in top_niches:
            print(f"  {niche}: {count}")
    else:
        print("  none yet")
    print("\nNewest Products:")
    for product in recent:
        filename = product.get("filename") or product.get("image_path") or "unknown"
        print(f"  #{product.get('id')} {filename} [{product.get('status')}]")
    print("\nRecommended Actions:")
    for action in recommendations:
        print(f"  - {action}")

    return report


def schedule_founder_task(
    task_type: str,
    *,
    payload: dict | None = None,
    priority: str = "normal",
) -> str:
    """Founder Agent schedules work; Task Runner executes later."""
    return add_task(
        task_type,
        payload=payload or {},
        priority=priority,
        assigned_agent="founder_agent",
    )


def schedule_niche_research(keywords: list[str]) -> str:
    """Schedule niche research for explicit keyword candidates."""
    cleaned = [keyword.strip() for keyword in keywords if keyword.strip()]
    if not cleaned:
        raise ValueError("At least one keyword is required.")
    return schedule_founder_task("niche_research", payload={"keywords": cleaned}, priority="normal")


def schedule_generate_designs(niche: str, amount: int) -> str:
    """Schedule design generation without executing it."""
    niche = niche.strip()
    if not niche:
        raise ValueError("Niche is required.")
    if amount <= 0:
        raise ValueError("Amount must be greater than 0.")
    return schedule_founder_task(
        "generate_designs",
        payload={"niche": niche, "amount": amount},
        priority="normal",
    )


def schedule_generate_mockups(product_ids: list[str | int]) -> list[str]:
    """Schedule one create_mockups task per product id."""
    cleaned = [str(product_id).strip() for product_id in product_ids if str(product_id).strip()]
    if not cleaned:
        raise ValueError("At least one product id is required.")
    return [
        schedule_founder_task(
            "generate_mockups",
            payload={"product_id": product_id},
            priority="high",
        )
        for product_id in cleaned
    ]


def schedule_generate_listing(product_id: str | int) -> str:
    """Schedule local listing template generation for one product."""
    product_id = str(product_id).strip()
    if not product_id:
        raise ValueError("Product id is required.")
    return schedule_founder_task(
        "generate_listing",
        payload={"product_id": product_id},
        priority="normal",
    )


def schedule_analytics_refresh() -> str:
    """Schedule a low-priority local analytics refresh."""
    return schedule_founder_task("analytics_refresh", payload={}, priority="low")


def schedule_batch_generation(niche: str, amount: int) -> str:
    """Create a production batch and schedule generation for it."""
    batch_id = create_batch(niche, amount)
    return schedule_founder_task(
        "batch_generation",
        payload={"batch_id": batch_id, "niche": niche, "amount": amount},
        priority="normal",
    )


def schedule_batch_review(batch_id: str) -> list[str]:
    """Schedule review tasks for products in a batch."""
    products = get_batch_products(batch_id)
    return [
        schedule_founder_task("review_product", payload={"product_id": product["id"]}, priority="normal")
        for product in products
    ]


def schedule_batch_mockups(batch_id: str) -> list[str]:
    """Schedule mockup tasks for products in a batch."""
    products = get_batch_products(batch_id)
    return [
        schedule_founder_task("generate_mockups", payload={"product_id": product["id"]}, priority="high")
        for product in products
    ]


def founder_task_report() -> dict[str, object]:
    """Print task queue/history health for the Founder Agent."""
    pending = get_pending_tasks()
    running = get_running_tasks()
    completed = get_completed_tasks()
    failed = get_failed_tasks()
    recent = get_recent_tasks(limit=5)
    next_task = get_next_task()
    success_rate = task_success_rate()
    recommendations = task_recommendations()
    structured_recommendations = generate_founder_recommendations()

    report = {
        "pending_tasks": len(pending),
        "running_tasks": len(running),
        "completed_tasks": len(completed),
        "failed_tasks": len(failed),
        "recent_tasks": recent,
        "task_success_rate": success_rate,
        "average_task_duration": average_task_duration(),
        "most_common_failures": most_common_failures(),
        "most_common_failure_type": most_common_failure_type(),
        "tasks_completed_today": tasks_completed_today(),
        "oldest_pending_task_age_seconds": pending_task_age_seconds(pending),
        "highest_priority_task": next_task,
        "recommended_action": structured_recommendations[0]["action"] if structured_recommendations else recommendations[0],
        "suggested_tasks": structured_recommendations,
    }

    print("\n=== AI FACTORY TASK REPORT ===\n")
    print(f"Pending Tasks: {report['pending_tasks']}")
    print(f"Running Tasks: {report['running_tasks']}")
    print(f"Completed Tasks: {report['completed_tasks']}")
    print(f"Failed Tasks: {report['failed_tasks']}")
    print(f"\nTask Success Rate: {round(success_rate * 100, 1)}%")
    print(f"Tasks Completed Today: {report['tasks_completed_today']}")
    print(f"Oldest Pending Task Age: {report['oldest_pending_task_age_seconds']}s")
    print(f"Most Common Failure: {report['most_common_failure_type']}")
    print("\nHighest Priority Task:")
    if next_task:
        print(f"{next_task.get('priority')} {next_task.get('type')} ({next_task.get('id')})")
    else:
        print("none")
    print("\nRecommended Founder Action:")
    print(report["recommended_action"])

    return report


def founder_niche_recommendations(keywords: list[str]) -> list[dict[str, object]]:
    """
    Research and rank candidate niches before generating designs.

    This uses public Etsy title signals only. It does not call OpenAI, upload
    products, or generate images.
    """
    reports = save_niche_report(keywords)

    print("\n=== NICHE RESEARCH REPORT ===\n")
    for index, row in enumerate(reports, start=1):
        print(f"{index}. {row['keyword']}")
        print(f"   Score: {row['score']}")
        print(f"   Demand: {row['demand_score']}")
        print(f"   Competition: {row['competition_level']}")
        print(f"   Trends: {row['trend_keywords'] or 'none detected'}")
        print(f"   Recommendation: {row['recommendation']}")

    if reports:
        best = reports[0]
        print("\nFounder recommendation:")
        print(f"Prioritize: {best['keyword']} ({best['recommendation']})")

    return reports


def print_founder_report() -> dict[str, int]:
    """Print current local product health and return the metrics."""
    metrics = get_founder_metrics()

    print("\n=== FOUNDER AGENT REPORT ===")
    print(f"Total products: {metrics['total_products']}")
    print(f"Drafts:         {metrics['drafts']}")
    print(f"Niches:         {metrics['niches']}")
    print("\nRecommended next action:")
    print(recommend_next_action(metrics))

    return metrics


def request_bulk_designs(niche: str, amount: int) -> str:
    """
    Schedule design generation. Task Runner executes the actual work later.
    """
    print("\n=== FOUNDER AGENT ===")
    print(f"Scheduling {amount} design(s) for niche: {niche}")

    task_id = schedule_generate_designs(niche, amount)
    print(f"Created task: {task_id}")
    return task_id


def run_founder_agent_cli() -> None:
    """Interactive Founder Agent CLI."""
    founder_dashboard()
    founder_task_report()

    answer = input("\nGenerate more designs now? (y/n): ").strip().lower()
    if answer != "y":
        return

    niche = input("What niche should we attack?: ").strip()
    amount = int(input("How many designs should the Design Agent create?: "))
    request_bulk_designs(niche, amount)


if __name__ == "__main__":
    run_founder_agent_cli()
