"""Concise Founder command briefings."""

from __future__ import annotations

from ai_factory.agents.founder_decision_center import generate_scaling_readiness_report
from ai_factory.agents.founder_intelligence import generate_growth_opportunities, generate_quality_alerts, generate_risk_report
from ai_factory.analytics.operational_scorecard import generate_operational_scorecard
from ai_factory.intelligence.priority_engine import generate_priority_queue
from ai_factory.maintenance.inventory_hygiene import generate_inventory_hygiene_report
from ai_factory.signals.product_signal_engine import rank_products_by_signal
from ai_factory.signals.validation_score import rank_validated_products
from ai_factory.intelligence.product_selector import select_products_for_listing
from ai_factory.products.product_manager import read_products
from ai_factory.review.design_improvement import analyze_design_weaknesses, suggest_design_improvements


def generate_daily_briefing() -> dict[str, object]:
    scorecard = generate_operational_scorecard()
    return {
        "headline": "Focus on cleanup and signal validation before scaling.",
        "operational_score": scorecard["overall_score"],
        "top_priority": generate_priority_queue()[0] if generate_priority_queue() else None,
        "top_opportunity": generate_top_opportunities()[:1],
        "biggest_risk": generate_biggest_risks()[:1],
    }


def generate_inventory_alerts() -> list[dict[str, object]]:
    hygiene = generate_inventory_hygiene_report()
    return [
        {"alert": "duplicate products detected", "count": hygiene["duplicate_count"]},
        {"alert": "cleanup candidates", "count": len(hygiene["cleanup_candidates"])},
        {"alert": "incomplete listings", "count": len(hygiene["incomplete_listings"])},
    ]


def generate_top_opportunities() -> list[dict[str, object]]:
    signals = rank_products_by_signal()[:5]
    validated = rank_validated_products()[:5]
    growth = generate_growth_opportunities()
    return [{"signals": signals, "validated_products": validated, "growth_recommendations": growth}]


def generate_biggest_risks() -> list[dict[str, object]]:
    return generate_risk_report()


def generate_cleanup_priorities() -> list[dict[str, object]]:
    hygiene = generate_inventory_hygiene_report()
    return [
        {"product_id": product.get("id"), "reason": "cleanup candidate"}
        for product in hygiene["cleanup_candidates"][:10]
    ]


def products_to_push() -> list[dict[str, object]]:
    return [row for row in rank_validated_products() if row["validation_level"] in {"promising", "validated", "scaling_candidate"}]


def products_to_pause() -> list[dict[str, object]]:
    return [row for row in rank_validated_products() if row["validation_level"] == "weak"]


def products_to_archive() -> list[dict[str, object]]:
    return generate_cleanup_priorities()


def experiments_to_run() -> list[dict[str, object]]:
    return [{"experiment_type": "small_niche_test", "reason": "Run low-risk validation batches only after cleanup."}]


def experiments_to_stop() -> list[dict[str, object]]:
    return [{"reason": "Stop experiments with no views/favorites/orders after a reasonable manual observation period."}]


def strongest_real_world_signals() -> list[dict[str, object]]:
    return rank_validated_products()[:5]


def weakest_inventory_risks() -> list[dict[str, object]]:
    return generate_cleanup_priorities()[:5]


def generate_execution_recommendation() -> dict[str, object]:
    """Practical next-step guidance for getting to first sale."""
    selection = select_products_for_listing(limit=3)
    hygiene = generate_inventory_hygiene_report()
    top_uploads = selection["recommended_uploads"][:3]
    rejected = selection["rejected_products"][:5]
    signals = strongest_real_world_signals()
    niche = top_uploads[0]["niche"] if top_uploads else "unknown"
    return {
        "top_3_products_to_manually_upload": top_uploads,
        "products_not_worth_uploading": rejected,
        "most_promising_niche": niche,
        "biggest_quality_issue": "low quality / missing mockups" if hygiene["cleanup_candidates"] else "none obvious",
        "biggest_duplicate_risk": hygiene["duplicate_count"],
        "fastest_path_to_first_sale": "Export packages for the best 3 products, manually list them, then update listing metrics after 24-72 hours.",
        "strongest_real_world_signals": signals,
    }


def generate_repair_recommendations() -> dict[str, object]:
    """Practical repair guidance for getting a few products upload-ready."""
    products = [product for product in read_products() if product.get("status") not in {"archived", "sold"}]
    analyses = []
    for product in products:
        try:
            analysis = analyze_design_weaknesses(product["id"])
        except (ValueError, KeyError):
            continue
        blocker_count = len(analysis["upload_blockers"])
        signal_score = float(analysis["signal"]["signal_score"])
        analyses.append({"product": product, "analysis": analysis, "repair_score": signal_score - blocker_count * 10})

    repairable = sorted(
        [row for row in analyses if row["analysis"]["upload_blockers"] and len(row["analysis"]["upload_blockers"]) <= 3],
        key=lambda row: float(row["repair_score"]),
        reverse=True,
    )
    beyond_repair = sorted(
        [row for row in analyses if len(row["analysis"]["upload_blockers"]) > 3],
        key=lambda row: float(row["repair_score"]),
    )
    easiest = repairable[0] if repairable else (sorted(analyses, key=lambda row: len(row["analysis"]["upload_blockers"]))[:1] or [None])[0]
    blocker_counts: dict[str, int] = {}
    for row in analyses:
        for blocker in row["analysis"]["upload_blockers"]:
            blocker_counts[blocker] = blocker_counts.get(blocker, 0) + 1
    biggest_blocker = max(blocker_counts.items(), key=lambda item: item[1])[0] if blocker_counts else "none obvious"

    return {
        "top_products_worth_repairing": [
            {
                "product_id": row["product"]["id"],
                "niche": row["product"].get("niche"),
                "upload_blockers": row["analysis"]["upload_blockers"],
                "suggestions": suggest_design_improvements(row["product"]["id"])["recommendations"],
            }
            for row in repairable[:5]
        ],
        "products_beyond_repair": [
            {"product_id": row["product"]["id"], "upload_blockers": row["analysis"]["upload_blockers"]}
            for row in beyond_repair[:5]
        ],
        "easiest_product_to_get_upload_ready": None
        if not easiest
        else {"product_id": easiest["product"]["id"], "upload_blockers": easiest["analysis"]["upload_blockers"]},
        "fastest_path_to_first_listing": "Repair the easiest product, generate a clean mockup set, run readiness, export listing package, then upload manually.",
        "biggest_current_quality_blocker": biggest_blocker,
    }

