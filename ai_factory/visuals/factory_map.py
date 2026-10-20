"""Static HomeBase Factory Map generator.

This is a local visualization shell over the real AI Factory OS CSVs and
modules. It does not run workflows, call APIs, upload products, or start a web
server.
"""

from __future__ import annotations

import csv
import html
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from ai_factory import products
from ai_factory.config import PROJECT_ROOT
from ai_factory.products.product_manager import is_valid_product_row, read_products
from ai_factory.intelligence.factory_recommendations import generate_factory_recommendations
from ai_factory.intelligence.listing_health import summarize_listing_health
from ai_factory.intelligence.winning_pattern_detector import detect_winning_patterns

OUTPUT_DIR = PROJECT_ROOT / "visualizations"
FACTORY_MAP_HTML = OUTPUT_DIR / "homebase_factory_map.html"

CSV_FILES = [
    "products.csv",
    "listings.csv",
    "task_queue.csv",
    "workflow_history.csv",
    "task_history.csv",
    "signal_history.csv",
    "experiments.csv",
    "listing_change_history.csv",
    "production_batches.csv",
]

PIPELINE_STAGES = [
    ("ideation", "IDEATION"),
    ("generation", "GENERATION"),
    ("review", "REVIEW"),
    ("mockups", "MOCKUPS"),
    ("listing", "LISTING"),
    ("published", "PUBLISHED"),
    ("sales", "SALES"),
    ("archived", "ARCHIVED"),
]


from typing import Iterable, Union


def _read_csv(name: str | Path) -> list[dict[str, str]]:
    path = PROJECT_ROOT / name if isinstance(name, str) else name
    if not path.exists():
        return []
    if path.name == "products.csv":
        try:
            return [row for row in read_products(path) if is_valid_product_row(row)]
        except Exception:
            return []
    try:
        with path.open("r", encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f))
    except (csv.Error, OSError, UnicodeDecodeError):
        return []


def _csv_stat(name: str) -> dict[str, object]:
    path = PROJECT_ROOT / name
    rows = _read_csv(name)
    if not path.exists():
        return {"file": name, "rows": 0, "last_updated": "missing", "health": "missing"}
    last_updated = datetime.fromtimestamp(path.stat().st_mtime).replace(microsecond=0).isoformat()
    health = "healthy" if rows or path.stat().st_size > 0 else "empty"
    return {"file": name, "rows": len(rows), "last_updated": last_updated, "health": health}


def _int(value: str | int | float | None) -> int:
    try:
        return int(float(str(value or "0").strip() or 0))
    except ValueError:
        return 0


def _float(value: str | int | float | None) -> float:
    try:
        return float(str(value or "0").replace("$", "").replace(",", "").strip() or 0)
    except ValueError:
        return 0.0


def _status_counts(products: list[dict[str, str]]) -> dict[str, int]:
    counts = Counter((row.get("status") or "draft").strip().lower() for row in products)
    return {
        "draft": counts.get("draft", 0),
        "reviewed": counts.get("reviewed", 0),
        "mockup_ready": counts.get("mockup_ready", 0),
        "upload_ready": counts.get("upload_ready", 0),
        "uploaded": counts.get("uploaded", 0),
        "listed": counts.get("listed", 0),
        "sold": counts.get("sold", 0),
        "archived": counts.get("archived", 0),
    }


def _top_niche(products: list[dict[str, str]]) -> str:
    niches = Counter((row.get("niche") or "unknown").strip().lower() for row in products if row.get("niche"))
    return niches.most_common(1)[0][0] if niches else "none yet"


def _top_product(products: list[dict[str, str]], listings: list[dict[str, str]]) -> str:
    if listings:
        ranked = sorted(listings, key=lambda row: (_int(row.get("orders")), _int(row.get("favorites")), _int(row.get("views"))), reverse=True)
        product_id = ranked[0].get("product_id", "")
        product = next((row for row in products if row.get("id") == product_id), {})
        return product.get("title") or product.get("niche") or f"product {product_id}"
    if products:
        newest = sorted(products, key=lambda row: _int(row.get("id")), reverse=True)[0]
        return newest.get("title") or newest.get("filename") or newest.get("niche") or "newest product"
    return "none yet"


def _thumbnail_style(listings: list[dict[str, str]]) -> str:
    styles = Counter(
        (row.get("primary_thumbnail_style") or row.get("thumbnail_test_notes") or row.get("notes") or "").strip().lower()
        for row in listings
        if (row.get("primary_thumbnail_style") or row.get("thumbnail_test_notes") or row.get("notes") or "").strip()
    )
    return styles.most_common(1)[0][0] if styles else "not tracked yet"


def _task_counts(tasks: list[dict[str, str]]) -> dict[str, int]:
    counts = Counter((row.get("status") or "unknown").strip().lower() for row in tasks)
    return {
        "pending": counts.get("pending", 0) + counts.get("queued", 0),
        "running": counts.get("running", 0),
        "completed": counts.get("completed", 0),
        "failed": counts.get("failed", 0),
        "cancelled": counts.get("cancelled", 0),
    }


def _health_tone(value: int, warning_at: int = 1) -> str:
    return "hot" if value >= warning_at else "calm"


def _pipeline_stage(product: dict[str, str]) -> str:
    stage = (product.get("pipeline_stage") or "").strip().lower()
    if stage:
        return stage
    return {
        "draft": "generation",
        "reviewed": "review",
        "mockup_ready": "mockups",
        "upload_ready": "listing",
        "uploaded": "published",
        "listed": "published",
        "sold": "sales",
        "archived": "archived",
    }.get((product.get("status") or "draft").strip().lower(), "ideation")


def _pipeline_counts(products: list[dict[str, str]]) -> list[dict[str, object]]:
    counts = Counter(_pipeline_stage(product) for product in products)
    total = len(products) or 1
    bottleneck = max(counts, key=counts.get) if counts else "generation"
    return [
        {
            "id": stage,
            "label": label,
            "count": counts.get(stage, 0),
            "percent": round(counts.get(stage, 0) / total * 100, 1),
            "bottleneck": stage == bottleneck and counts.get(stage, 0) > 0,
            "active": counts.get(stage, 0) > 0,
        }
        for stage, label in PIPELINE_STAGES
    ]


def _best_signal_value(rows: list[dict[str, str]], field: str, fallback: str = "not tracked yet") -> str:
    values = Counter((row.get(field) or "").strip().lower() for row in rows if (row.get(field) or "").strip())
    return values.most_common(1)[0][0] if values else fallback


def _best_listing_rows(listings: list[dict[str, str]]) -> list[dict[str, object]]:
    ranked = sorted(
        listings,
        key=lambda row: (_int(row.get("orders")) * 100, _int(row.get("favorites")) * 10, _int(row.get("views"))),
        reverse=True,
    )
    return [
        {
            "listing_id": row.get("listing_id", "")[:8],
            "product_id": row.get("product_id", ""),
            "views": _int(row.get("views")),
            "favorites": _int(row.get("favorites")),
            "orders": _int(row.get("orders")),
            "conversion": round(_int(row.get("orders")) / max(1, _int(row.get("views"))), 4),
        }
        for row in ranked[:5]
    ]


def _listing_title(listing: dict[str, str], product_map: dict[str, dict[str, str]]) -> str:
    product = product_map.get(str(listing.get("product_id", "")), {})
    title = (product.get("title") or listing.get("marketplace_listing_id") or listing.get("listing_id") or "unknown listing").strip()
    return title


def _top_listing_by_field(listings: list[dict[str, str]], field: str, product_map: dict[str, dict[str, str]]) -> str:
    available = [row for row in listings if row.get(field) is not None]
    if not available:
        return "none yet"
    winner = max(available, key=lambda row: _float(row.get(field)))
    label = _listing_title(winner, product_map)
    return f"{label} ({winner.get(field, '0')})"


def _most_likely_next_sale(listings: list[dict[str, str]], product_map: dict[str, dict[str, str]]) -> str:
    candidates = []
    for row in listings:
        if (row.get("listing_status") or "").strip().lower() not in {"active", "uploaded"}:
            continue
        views = _int(row.get("views"))
        favorites = _int(row.get("favorites"))
        orders = _int(row.get("orders"))
        conversion = _float(row.get("conversion_rate"))
        score = conversion * 100 + favorites * 3 + views * 0.2 + orders * 8
        candidates.append((score, row))
    if not candidates:
        return "none yet"
    winner = max(candidates, key=lambda item: item[0])[1]
    return _listing_title(winner, product_map)


def _file_uri(path: Path) -> str:
    try:
        return path.resolve().as_uri()
    except Exception:
        return str(path)


def _validation_score(product: dict[str, str], listing: dict[str, str] | None = None) -> int:
    listing = listing or {}
    score = 0
    score += min(20, _int(product.get("quality_score")) * 4)
    score += min(30, _int(listing.get("favorites")) * 3)
    score += min(30, _int(listing.get("orders")) * 10)
    score += min(20, _int(listing.get("views")) // 5)
    return min(100, max(0, score))


def _stage_label(product: dict[str, str]) -> str:
    stage = (product.get("pipeline_stage") or product.get("status") or "").strip().lower()
    if not stage:
        return "Unknown"
    return stage.replace("_", " ").upper()


def _top_weakness(product: dict[str, str], listing: dict[str, str] | None = None) -> str:
    listing = listing or {}
    if _int(product.get("quality_score")) <= 0:
        return "Low quality"
    if not (product.get("mockup_paths") or "").strip():
        return "No mockups"
    if product.get("status") not in {"upload_ready", "uploaded", "listed", "sold"}:
        return "Needs upload readiness"
    if _int(listing.get("views")) < 10:
        return "Low listing exposure"
    return "Refine title / tags"


def _weakest_niche(products: list[dict[str, str]], listings: list[dict[str, str]], fallback: str = "none yet") -> str:
    niche_scores: dict[str, list[int]] = defaultdict(list)
    product_map = {row.get("id", ""): row for row in products}
    for listing in listings:
        product = product_map.get(str(listing.get("product_id", "")), {})
        niche = (product.get("niche") or "none yet").strip().lower() or "none yet"
        niche_scores[niche].append(_int(listing.get("orders")) * 10 + _int(listing.get("favorites")) * 3 + _int(listing.get("views")))
    if not niche_scores:
        return fallback
    return min(niche_scores.items(), key=lambda item: sum(item[1]) / max(1, len(item[1])))[0]


def _duplicate_risk(product: dict[str, str], products: list[dict[str, str]]) -> str:
    title = (product.get("title") or "").strip().lower()
    niche = (product.get("niche") or "").strip().lower()
    same_title = sum(1 for row in products if row.get("id") != product.get("id") and (row.get("title") or "").strip().lower() == title)
    same_niche = sum(1 for row in products if row.get("id") != product.get("id") and (row.get("niche") or "").strip().lower() == niche)
    if same_title:
        return "high"
    if same_niche >= 2:
        return "medium"
    return "low"


def _product_cards(products: list[dict[str, str]], listings: list[dict[str, str]], top_hook: str) -> list[dict[str, object]]:
    listing_map = {row.get("product_id", ""): row for row in listings}
    cards = []
    sorted_products = sorted(products, key=lambda row: (_float(row.get("estimated_profit")) or _float(row.get("actual_revenue")) or 0), reverse=True)
    for product in sorted_products[:10]:
        listing = listing_map.get(product.get("id", ""), {})
        cards.append({
            "product_id": product.get("id", ""),
            "title": product.get("title") or product.get("niche") or "untitled product",
            "niche": product.get("niche") or "general",
            "stage": _stage_label(product),
            "validation_level": _validation_score(product, listing),
            "revenue": round(_float(product.get("actual_revenue") or product.get("revenue")), 2),
            "thumbnail_style": (listing.get("primary_thumbnail_style") or listing.get("thumbnail_test_notes") or "not tracked yet"),
            "readiness_status": "upload ready" if product.get("status") == "upload_ready" else "repair needed" if _int(product.get("quality_score")) <= 0 or not (product.get("mockup_paths") or "").strip() else "validation candidate" if listing and _int(listing.get("views")) > 0 else "draft",
            "duplicate_risk": _duplicate_risk(product, products),
            "signal_strength": min(100, _int(listing.get("favorites")) * 18 + _int(listing.get("views")) // 4 + _int(listing.get("orders")) * 35),
            "top_weakness": _top_weakness(product, listing),
            "package_folder": _file_uri(PROJECT_ROOT / "exports" / f"product_{product.get('id', '')}"),
            "emotional_hook": product.get("niche") or top_hook,
        })
    return cards


def _listing_previews(products: list[dict[str, str]], listings: list[dict[str, str]], top_hook: str) -> list[dict[str, object]]:
    product_map = {row.get("id", ""): row for row in products}
    active = [row for row in listings if (row.get("listing_status") or "").lower() in {"active", "uploaded", "listed"}]
    ranked = sorted(active, key=lambda row: (_int(row.get("views")), _int(row.get("favorites")), _int(row.get("orders"))), reverse=True)
    previews = []
    for row in ranked[:6]:
        product = product_map.get(str(row.get("product_id", "")), {})
        previews.append({
            "listing_id": row.get("listing_id", ""),
            "product_title": product.get("title") or product.get("niche") or "untitled",
            "thumbnail_style": (row.get("primary_thumbnail_style") or row.get("thumbnail_test_notes") or "not tracked yet"),
            "views": _int(row.get("views")),
            "favorites": _int(row.get("favorites")),
            "orders": _int(row.get("orders")),
            "conversion_rate": float(row.get("conversion_rate") or 0) or round(_int(row.get("orders")) / max(1, _int(row.get("views"))), 4),
            "validation_score": _validation_score(product, row),
            "emotional_hook": product.get("niche") or top_hook,
        })
    return previews


def _experiment_timeline(changes: list[dict[str, str]], products: list[dict[str, str]], listings: list[dict[str, str]]) -> list[dict[str, object]]:
    product_map = {row.get("id", ""): row for row in products}
    listing_map = {row.get("listing_id", ""): row for row in listings}
    events = []
    for row in changes:
        if not row.get("changed_at"):
            continue
        actions = []
        if row.get("title_after") and row.get("title_after") != row.get("title_before"):
            actions.append("Title")
        if row.get("tags_after") and row.get("tags_after") != row.get("tags_before"):
            actions.append("Tags")
        if row.get("thumbnail_after") and row.get("thumbnail_after") != row.get("thumbnail_before"):
            actions.append("Thumbnail")
        if not actions:
            continue
        product = product_map.get(str(row.get("product_id", "")), {})
        listing = listing_map.get(row.get("listing_id", ""), {})
        events.append({
            "changed_at": row.get("changed_at"),
            "product_title": product.get("title") or product.get("niche") or "untitled",
            "change_type": " / ".join(actions),
            "reason": row.get("reason_for_change") or "experiment update",
            "metrics": f"views:{_int(listing.get('views'))} favorites:{_int(listing.get('favorites'))} orders:{_int(listing.get('orders'))}",
            "details": row.get("title_after") or row.get("tags_after") or row.get("thumbnail_after") or "change recorded",
        })
    return sorted(events, key=lambda item: item.get("changed_at", ""), reverse=True)[:8]


def _readiness_queue(products: list[dict[str, str]], listings: list[dict[str, str]]) -> dict[str, list[str]]:
    listing_map = {row.get("product_id", ""): row for row in listings}
    product_map = {row.get("id", ""): row for row in products}
    upload_ready = [row.get("title") or row.get("niche") or "untitled" for row in products if row.get("status") == "upload_ready"]
    repair_needed = [row.get("title") or row.get("niche") or "untitled" for row in products if _int(row.get("quality_score")) <= 0 or not (row.get("mockup_paths") or "").strip()]
    archive_suggested = [row.get("title") or row.get("niche") or "untitled" for row in products if row.get("status") not in {"archived", "sold"} and _int(row.get("quality_score")) <= 0 and not (row.get("mockup_paths") or "").strip()]
    validation_candidate = [product_map.get(str(row.get("product_id", "")), {}).get("title") or product_map.get(str(row.get("product_id", "")), {}).get("niche") or row.get("product_id") for row in listings if (row.get("listing_status") or "").lower() in {"active", "uploaded", "listed"} and _int(row.get("views")) > 0 and _int(row.get("orders")) == 0]
    scaling_candidate = [product_map.get(str(row.get("product_id", "")), {}).get("title") or product_map.get(str(row.get("product_id", "")), {}).get("niche") or row.get("product_id") for row in listings if _int(row.get("orders")) > 0 or _int(row.get("favorites")) >= 3]
    return {
        "upload_ready": upload_ready[:3],
        "repair_needed": repair_needed[:3],
        "archive_suggested": archive_suggested[:3],
        "validation_candidate": validation_candidate[:3],
        "scaling_candidate": scaling_candidate[:3],
    }


def _operational_score(
    products: list[dict[str, str]],
    listings: list[dict[str, str]],
    tasks: list[dict[str, str]],
) -> int:
    total_products = len(products) or 1
    listed_or_uploaded = len([row for row in products if row.get("status") in {"upload_ready", "uploaded", "listed", "sold"}])
    active_listings = len([row for row in listings if (row.get("listing_status") or "").lower() in {"active", "uploaded"}])
    failed_tasks = len([row for row in tasks if (row.get("status") or "").lower() == "failed"])
    revenue_signal = min(25, int(sum(_float(row.get("revenue")) for row in listings) * 2))
    readiness = min(35, int(listed_or_uploaded / total_products * 35))
    market = min(25, active_listings * 10 + sum(_int(row.get("orders")) for row in listings) * 10)
    reliability = max(0, 15 - failed_tasks * 5)
    return min(100, readiness + market + revenue_signal + reliability)


def _ready_to_scale(listings: list[dict[str, str]]) -> str:
    if any(_int(row.get("orders")) > 0 for row in listings):
        return "small cluster expansion"
    if any(_int(row.get("favorites")) >= 3 for row in listings):
        return "optimize before scaling"
    return "collect market signal"


def _product_label(product: dict[str, str]) -> str:
    return product.get("title") or product.get("niche") or product.get("filename") or f"product {product.get('id', '')}"


def _execution_mode(
    products: list[dict[str, str]],
    listings: list[dict[str, str]],
    task_counts: dict[str, int],
    status_counts: dict[str, int],
) -> dict[str, object]:
    upload_candidates = [_product_label(row) for row in products if row.get("status") == "upload_ready"][:3]
    archive_candidates = [_product_label(row) for row in products if _int(row.get("quality_score")) <= 0 and row.get("status") != "archived"][:3]
    has_views_no_faves = [row for row in listings if _int(row.get("views")) >= 25 and _int(row.get("favorites")) == 0 and _int(row.get("orders")) == 0]
    top_listing = _best_listing_rows(listings)[:1]
    actions = []
    if has_views_no_faves:
        actions.append("Improve primary thumbnail on high-view listing with no favorites.")
    if upload_candidates:
        actions.append("Export package and manually upload the strongest upload-ready product.")
    if top_listing and top_listing[0]["favorites"]:
        actions.append("Create one nearby emotional variant for the strongest engaged listing.")
    if not actions:
        actions.append("Import fresh Etsy metrics, then change only one listing variable.")
    actions.append("Record every title/tag/thumbnail change before the next metric check.")
    actions.append("Pause or archive weak clutter before generating large batches.")
    bottleneck = "tasks failing" if task_counts["failed"] else "draft/review backlog" if status_counts["draft"] + status_counts["reviewed"] else "market signal collection"
    return {
        "next_actions": actions[:3],
        "highest_leverage_fix": actions[0],
        "products_to_upload": upload_candidates,
        "products_to_archive": archive_candidates,
        "current_experiment": "cute emotional sticker sheet validation",
        "biggest_bottleneck": bottleneck,
    }


def collect_factory_map_data() -> dict[str, object]:
    """Collect read-only data for the visual factory map."""

    products = _read_csv("products.csv")
    listings = _read_csv("listings.csv")
    tasks = _read_csv("task_queue.csv")
    workflows = _read_csv("workflow_history.csv")
    signals = _read_csv("signal_history.csv")
    listing_change_history = _read_csv("listing_change_history.csv")
    status_counts = Counter()
    for product in products:
        stage = product.get("pipeline_stage", "unknown")
        status_counts[stage] += 1
    pipeline = _pipeline_counts(products)
    task_counts = _task_counts(tasks)
    experiments = _read_csv("experiments.csv")
    revenue = round(sum(_float(row.get("revenue") or row.get("actual_revenue")) for row in listings), 2)
    if revenue == 0:
        revenue = round(sum(_float(row.get("actual_revenue") or row.get("revenue")) for row in products), 2)
    active_listings = len([row for row in listings if (row.get("listing_status") or "").lower() in {"active", "uploaded"}])
    etsy_listings = [row for row in listings if (row.get("platform") or "").strip().lower() == "etsy"]
    imported_etsy_listings = len(etsy_listings)
    imported_active_etsy = len([row for row in etsy_listings if (row.get("listing_status") or "").lower() in {"active", "uploaded"}])
    imported_favorites = sum(_int(row.get("favorites")) for row in etsy_listings)
    imported_orders = sum(_int(row.get("orders")) for row in etsy_listings)
    imported_revenue = round(sum(_float(row.get("revenue")) for row in etsy_listings), 2)
    validation_count = len([row for row in products if _int(row.get("total_orders")) > 0 or _int(row.get("actual_sales_count")) > 0])
    favorites = sum(_int(row.get("favorites")) for row in listings)
    orders = sum(_int(row.get("orders")) for row in listings)
    views = sum(_int(row.get("views")) for row in listings)
    conversion = round(orders / views, 4) if views else 0.0
    top_niche = _top_niche(products)
    product_map = {row.get("id", ""): row for row in products}
    top_viewed_listing = _top_listing_by_field(etsy_listings, "views", product_map)
    top_favorited_listing = _top_listing_by_field(etsy_listings, "favorites", product_map)
    top_converting_listing = _top_listing_by_field(etsy_listings, "conversion_rate", product_map)
    most_likely_next_sale = _most_likely_next_sale(etsy_listings, product_map)
    health_summary = summarize_listing_health(etsy_listings)
    recommendations = generate_factory_recommendations(etsy_listings, products)
    winning_patterns = detect_winning_patterns()
    top_hook_data = winning_patterns.get("top_emotional_hook") if isinstance(winning_patterns, dict) else None
    top_hook = (
        top_hook_data.get("value")
        if top_hook_data and top_hook_data.get("value") and top_hook_data.get("value") != "unknown"
        else _best_signal_value(products, "niche", top_niche)
    )
    top_thumbnail = (
        (winning_patterns.get("top_thumbnail_style") or {}).get("value")
        if isinstance(winning_patterns, dict)
        else None
    )
    if not top_thumbnail or top_thumbnail == "unknown":
        top_thumbnail = _thumbnail_style(listings)
    operational_score = _operational_score(products, listings, tasks)
    ready_to_scale = _ready_to_scale(listings)
    best_listings = _best_listing_rows(listings)
    product_cards = _product_cards(products, listings, top_hook)
    listing_previews = _listing_previews(products, listings, top_hook)
    experiment_timeline = _experiment_timeline(listing_change_history, products, listings)
    readiness_queue = _readiness_queue(products, listings)
    validation_count = len([row for row in products if _int(row.get("quality_score")) > 0 or _int(row.get("total_orders")) > 0 or _int(row.get("actual_sales_count")) > 0])
    validation_progress = min(100, int(validation_count / max(1, len(products)) * 100)) if products else 0
    listing_readiness_progress = min(100, int(status_counts["upload_ready"] / max(1, len(products)) * 100)) if products else 0
    signal_strength_progress = min(100, int(min(1.0, max(0.0, favorites / max(1, views))) * 70 + min(30, orders * 10))) if listings else 0
    operation_progress = operational_score
    market_panels = [
        {
            "name": "Etsy",
            "status": "manual live",
            "count": active_listings,
            "signal": min(100, favorites * 10 + orders * 15),
            "revenue": revenue,
            "emoji": "🛒",
        },
        {
            "name": "Printify",
            "status": "manual candidate",
            "count": len([row for row in products if row.get("platform") == "printify"]),
            "signal": 20 if active_listings else 8,
            "revenue": 0,
            "emoji": "📦",
        },
        {
            "name": "Digital Downloads",
            "status": "adjacent test",
            "count": len([row for row in products if row.get("type") == "digital"]),
            "signal": 15 if validation_count else 5,
            "revenue": 0,
            "emoji": "💾",
        },
        {
            "name": "Experiments",
            "status": "tracked",
            "count": len(experiments),
            "signal": min(100, len(experiments) * 12),
            "revenue": 0,
            "emoji": "🧪",
        },
    ]
    execution_mode = _execution_mode(products, listings, task_counts, status_counts)
    factory_status = "Awaiting Market Signal" if not listings else "Awaiting first validation" if validation_count == 0 else "Signal gathering in progress"
    current_focus = execution_mode["highest_leverage_fix"]
    top_action = execution_mode["next_actions"][0] if execution_mode["next_actions"] else "Maintain current manual path"
    money_flow = [
        {"step": "Idea", "status": "seed"},
        {"step": "Product", "status": "ready"},
        {"step": "Mockup", "status": "ready"},
        {"step": "Listing", "status": "live" if listings else "idle"},
        {"step": "Views", "status": views and views > 0 and "active" or "cold"},
        {"step": "Favorites", "status": favorites and favorites > 0 and "warming" or "weak"},
        {"step": "Orders", "status": orders and orders > 0 and "emerging" or "dry"},
        {"step": "Revenue", "status": revenue and revenue > 0 and "flowing" or "waiting"},
    ]
    csv_stats = [_csv_stat(name) for name in CSV_FILES]
    hook_score = 80
    if top_hook_data and top_hook_data.get("average_signal") is not None:
        try:
            hook_score = min(100, int(float(top_hook_data["average_signal"]) * 20))
        except (TypeError, ValueError):
            hook_score = 80 if top_hook != "none yet" else 20
    signal_heatmap = [
        {"label": "Strongest niche", "value": top_niche, "score": 82 if top_niche != "none yet" else 20, "tone": "purple"},
        {"label": "Emotional hook", "value": top_hook, "score": hook_score if top_hook != "none yet" else 20, "tone": "purple"},
        {"label": "Thumbnail style", "value": top_thumbnail, "score": 75 if top_thumbnail != "not tracked yet" else 25, "tone": "cyan"},
        {"label": "Best CTR candidate", "value": best_listings[0]["listing_id"] if best_listings else "none yet", "score": min(100, int(conversion * 1000)) if conversion else 15, "tone": "green"},
        {"label": "Favorite signal", "value": f"{favorites} favorites", "score": min(100, favorites * 12), "tone": "orange" if favorites == 0 else "green"},
    ]

    rooms = [
        {
            "id": "founder",
            "name": "Founder Command Center",
            "modules": ["Founder Agent", "Founder Briefing", "Weekly Review", "Daily Execution Brief"],
            "stats": {
                "Operational focus": "first validated listing",
                "Revenue": f"${revenue}",
                "Top product": _top_product(products, listings),
                "Top niche": top_niche,
            },
            "details": {
                "Founder briefing": "Focus on real listing signal, not more architecture.",
                "Weekly review": "Check winners, weak listings, profit, and next three manual actions.",
                "Daily priority": execution_mode["highest_leverage_fix"],
                "Ready to scale": ready_to_scale,
            },
            "recommendation": "Improve the strongest live listing before generating more inventory.",
            "tone": "healthy" if operational_score >= 65 else "warning",
        },
        {
            "id": "generation",
            "name": "Product Generation Bay",
            "modules": ["Bulk Generator", "Variant Generator", "Product Selector", "Repair Workflow"],
            "stats": {
                "Drafts": status_counts["draft"],
                "Reviewed": status_counts["reviewed"],
                "Upload-ready": status_counts["upload_ready"],
                "Total products": len(products),
            },
            "details": {
                "Product selector": "Ranks products for manual upload.",
                "Repair workflow": "Schedules repair tasks only; no autonomous execution.",
                "Variant rule": "Only generate nearby emotional variants after engagement.",
                "Draft pressure": status_counts["draft"],
            },
            "recommendation": "Generate only close variants around proven emotional hooks.",
            "tone": "warning" if status_counts["draft"] >= 10 else "healthy",
        },
        {
            "id": "studio",
            "name": "Mockup & Listing Studio",
            "modules": ["Mockup Generator", "Listing Generator", "SEO Optimizer", "Thumbnail Analyzer"],
            "stats": {
                "Top thumbnail style": top_thumbnail,
                "Products with mockups": len([row for row in products if row.get("mockup_paths")]),
                "Listings tracked": len(listings),
                "Active listings": active_listings,
            },
            "details": {
                "SEO optimizer": "Scores title readability, tags, and keyword repetition.",
                "Thumbnail analyzer": "Uses tracked style notes and real Etsy metrics.",
                "Readiness count": status_counts["upload_ready"],
                "Best style": top_thumbnail,
            },
            "recommendation": "Test close-up, sticker-focused thumbnails first.",
            "tone": "healthy" if active_listings else "warning",
        },
        {
            "id": "signals",
            "name": "Market Signal Lab",
            "modules": ["Signal Engine", "Validation Scores", "Early Winner Detector", "Revenue Tracker", "Winning Pattern Detector"],
            "stats": {
                "Views": views,
                "Favorites": favorites,
                "Orders": orders,
                "Conversion": conversion,
            },
            "details": {
                "Strongest listings": best_listings,
                "Signal rows": len(signals),
                "Validated products": validation_count,
                "Winning pattern": top_hook,
            },
            "recommendation": "Treat favorites and views as early signal before scaling.",
            "tone": "healthy" if favorites or orders else "warning",
        },
        {
            "id": "workflow",
            "name": "Workflow Pipeline",
            "modules": ["Workflow Engine", "Task Queue", "Task Runner", "Task History"],
            "stats": {
                "Pending tasks": task_counts["pending"],
                "Running tasks": task_counts["running"],
                "Completed tasks": task_counts["completed"],
                "Active workflows": len([row for row in workflows if row.get("status") in {"pending", "running"}]),
            },
            "details": {
                "Queued work": task_counts["pending"],
                "Failures": task_counts["failed"],
                "Bottleneck": execution_mode["biggest_bottleneck"],
                "Latest workflows": len(workflows),
            },
            "recommendation": "Run one explicit task at a time; no background loops.",
            "tone": "danger" if task_counts["failed"] else "healthy",
        },
        {
            "id": "storage",
            "name": "Storage / Memory Vault",
            "modules": ["products.csv", "listings.csv", "task_queue.csv", "workflow_history.csv", "signal_history.csv", "experiments.csv"],
            "stats": {
                "CSV files tracked": len(CSV_FILES),
                "CSV rows total": sum(int(stat["rows"]) for stat in csv_stats),
                "Signal rows": len(signals),
                "Experiments": len(experiments),
            },
            "details": {
                "Memory model": "CSV-backed local source of truth.",
                "Missing files": len([stat for stat in csv_stats if stat["health"] == "missing"]),
                "Healthy files": len([stat for stat in csv_stats if stat["health"] == "healthy"]),
                "Last updated": max((str(stat["last_updated"]) for stat in csv_stats if stat["last_updated"] != "missing"), default="not yet"),
            },
            "recommendation": "CSV memory is the local source of truth.",
            "tone": "healthy",
        },
        {
            "id": "market",
            "name": "Market Output Terminals",
            "modules": ["Etsy", "Printify", "Gumroad", "Digital Downloads"],
            "stats": {
                "Live/manual listings": active_listings,
                "Estimated revenue": f"${revenue}",
                "Validated products": validation_count,
                "Products needing updates": status_counts["draft"] + status_counts["reviewed"],
            },
            "details": {
                "Etsy": f"{active_listings} manual listings",
                "Printify": "manual fulfillment path",
                "Gumroad": "candidate digital-download lane",
                "Digital Downloads": "best adjacent low-friction test",
            },
            "recommendation": "Use Etsy manually now; add Gumroad/digital downloads as adjacent tests.",
            "tone": "healthy" if active_listings else "warning",
        },
    ]

    return {
        "generated_at": datetime.now().replace(microsecond=0).isoformat(),
        "rooms": rooms,
        "csv_stats": csv_stats,
        "pipeline": pipeline,
        "signal_heatmap": signal_heatmap,
        "execution_mode": execution_mode,
        "market_outputs": [
            {"name": "Etsy", "status": "manual live", "count": active_listings, "metric": "tracked listings"},
            {"name": "Printify", "status": "manual", "count": orders, "metric": "orders"},
            {"name": "Gumroad", "status": "candidate", "count": 0, "metric": "digital tests"},
            {"name": "Digital Downloads", "status": "candidate", "count": 0, "metric": "packs"},
        ],
        "market_panels": market_panels,
        "money_flow": money_flow,
        "factory_status": factory_status,
        "scale_readiness": ready_to_scale,
        "current_focus": current_focus,
        "top_action": top_action,
        "validation_progress": validation_progress,
        "listing_readiness_progress": listing_readiness_progress,
        "signal_strength_progress": signal_strength_progress,
        "operational_score": operation_progress,
        "product_cards": product_cards,
        "listing_previews": listing_previews,
        "experiment_timeline": experiment_timeline,
        "readiness_queue": readiness_queue,
        "etsy_sync": {
            "imported_etsy_listings": imported_etsy_listings,
            "imported_active_etsy": imported_active_etsy,
            "imported_favorites": imported_favorites,
            "imported_orders": imported_orders,
            "imported_revenue": imported_revenue,
            "top_viewed_listing": top_viewed_listing,
            "top_favorited_listing": top_favorited_listing,
            "top_converting_listing": top_converting_listing,
            "most_likely_next_sale": most_likely_next_sale,
        },
        "listing_health": health_summary,
        "recommendations": recommendations,
        "summary": {
            "products": len(products),
            "listings": len(listings),
            "tasks": len(tasks),
            "workflows": len(workflows),
            "revenue": revenue,
            "real_revenue": revenue,
            "active_listings": active_listings,
            "validation_count": validation_count,
            "top_niche": top_niche,
            "top_emotional_hook": top_hook,
            "operational_score": operational_score,
            "ready_to_scale": ready_to_scale,
        },
    }


def _json_script(data: dict[str, object]) -> str:
    return html.escape(json.dumps(data), quote=False)


def _render_html(data: dict[str, object]) -> str:
    payload = _json_script(data)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>HomeBase Factory Map</title>
  <style>
    :root {{
      --bg: #080d14;
      --panel: #101925;
      --panel-2: #0c141e;
      --text: #edf6ff;
      --muted: #8fa6b8;
      --line: #284155;
      --accent: #3ee7c4;
      --accent-2: #6ea8ff;
      --warn: #ffcf70;
      --hot: #ff7a90;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: radial-gradient(circle at top left, #152235 0, var(--bg) 38%);
      color: var(--text);
    }}
    .shell {{ max-width: 1440px; margin: 0 auto; padding: 28px; }}
    .topbar {{ display: flex; justify-content: space-between; gap: 18px; align-items: flex-start; margin-bottom: 24px; }}
    h1 {{ margin: 0; font-size: 28px; letter-spacing: 0.02em; }}
    .subtitle {{ margin: 8px 0 0; color: var(--muted); max-width: 820px; line-height: 1.5; }}
    .stamp {{ color: var(--muted); font-size: 13px; text-align: right; }}
    .stats {{ display: grid; grid-template-columns: repeat(5, minmax(120px, 1fr)); gap: 12px; margin: 20px 0 24px; }}
    .stat {{ background: rgba(16, 25, 37, 0.86); border: 1px solid var(--line); border-radius: 14px; padding: 14px; }}
    .stat b {{ display: block; font-size: 22px; margin-bottom: 4px; }}
    .stat span {{ color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; }}
    .layout {{ display: grid; grid-template-columns: 1.5fr 0.8fr; gap: 18px; align-items: start; }}
    .factory {{ position: relative; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; padding: 16px; border: 1px solid var(--line); border-radius: 22px; background: rgba(8, 13, 20, 0.72); }}
    .factory::before {{ content: ""; position: absolute; inset: 50% 8% auto; border-top: 1px dashed rgba(62, 231, 196, 0.32); pointer-events: none; }}
    .room {{
      min-height: 188px;
      padding: 16px;
      border: 1px solid var(--line);
      border-radius: 18px;
      background: linear-gradient(180deg, rgba(16,25,37,0.96), rgba(12,20,30,0.96));
      cursor: pointer;
      position: relative;
      transition: border-color 120ms ease, transform 120ms ease;
    }}
    .room:hover, .room.active {{ border-color: var(--accent); transform: translateY(-1px); }}
    .room.core::after {{ content: ""; position: absolute; right: 14px; top: 14px; width: 9px; height: 9px; border-radius: 99px; background: var(--accent); }}
    .room.hot::after {{ content: ""; position: absolute; right: 14px; top: 14px; width: 9px; height: 9px; border-radius: 99px; background: var(--hot); }}
    .room.calm::after {{ content: ""; position: absolute; right: 14px; top: 14px; width: 9px; height: 9px; border-radius: 99px; background: var(--muted); }}
    .room h2 {{ font-size: 16px; margin: 0 18px 12px 0; }}
    .modules {{ color: var(--muted); font-size: 12px; line-height: 1.45; margin-bottom: 14px; }}
    .room-stats {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }}
    .mini {{ border-top: 1px solid rgba(143, 166, 184, 0.2); padding-top: 8px; }}
    .mini span {{ color: var(--muted); display: block; font-size: 11px; }}
    .mini b {{ font-size: 14px; overflow-wrap: anywhere; }}
    .detail, .vault {{ border: 1px solid var(--line); border-radius: 20px; background: rgba(16,25,37,0.9); padding: 18px; }}
    .detail h2, .vault h2 {{ margin: 0 0 12px; font-size: 18px; }}
    .detail .recommendation {{ color: var(--accent); line-height: 1.5; margin: 14px 0; }}
    .detail-list {{ display: grid; gap: 10px; }}
    .detail-row {{ display: flex; justify-content: space-between; gap: 12px; border-bottom: 1px solid rgba(143,166,184,0.16); padding-bottom: 8px; }}
    .detail-row span {{ color: var(--muted); }}
    .detail-row b {{ text-align: right; overflow-wrap: anywhere; }}
    .vault {{ margin-top: 18px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    th, td {{ text-align: left; padding: 8px 6px; border-bottom: 1px solid rgba(143,166,184,0.14); }}
    th {{ color: var(--muted); font-weight: 600; }}
    .healthy {{ color: var(--accent); }}
    .missing {{ color: var(--warn); }}
    .empty {{ color: var(--muted); }}
    .actions {{ margin-top: 18px; color: var(--muted); font-size: 13px; line-height: 1.55; }}
    @media (max-width: 980px) {{
      .layout, .topbar {{ grid-template-columns: 1fr; display: block; }}
      .factory {{ grid-template-columns: 1fr; }}
      .stats {{ grid-template-columns: repeat(2, minmax(120px, 1fr)); }}
      .detail {{ margin-top: 18px; }}
    }}
  </style>
</head>
<body>
  <div class="shell">
    <header class="topbar">
      <div>
        <h1>HomeBase Factory Map</h1>
        <p class="subtitle">A local visual command center for the real AI Factory OS. This map reads CSV memory and module outputs only; it does not execute workflows, upload products, call APIs, or run background workers.</p>
      </div>
      <div class="stamp">Last synchronized<br><span id="generatedAt"></span></div>
    </header>
    <section class="stats" id="summary"></section>
    <main class="layout">
      <section class="factory" id="factory"></section>
      <aside>
        <section class="detail" id="detail"></section>
        <section class="vault">
          <h2>Storage / Memory Vault</h2>
          <table>
            <thead><tr><th>CSV</th><th>Rows</th><th>Health</th></tr></thead>
            <tbody id="csvStats"></tbody>
          </table>
        </section>
        <section class="actions">
          Explicit actions still run through the CLI. Use this map for orientation, then run the relevant CLI command for readiness checks, metric imports, listing exports, or weekly reviews.
        </section>
      </aside>
    </main>
  </div>
  <script id="factory-data" type="application/json">{payload}</script>
  <script>
    const data = JSON.parse(document.getElementById('factory-data').textContent);
    const factory = document.getElementById('factory');
    const detail = document.getElementById('detail');
    const summary = document.getElementById('summary');
    const csvStats = document.getElementById('csvStats');
    document.getElementById('generatedAt').textContent = data.generated_at;

    const summaryItems = [
      ['Products', data.summary.products],
      ['Listings', data.summary.listings],
      ['Tasks', data.summary.tasks],
      ['Workflows', data.summary.workflows],
      ['Revenue', '$' + data.summary.revenue]
    ];
    summary.innerHTML = summaryItems.map(([label, value]) => `<div class="stat"><b>${{value}}</b><span>${{label}}</span></div>`).join('');

    function renderRoom(room, index) {{
      const stats = Object.entries(room.stats).slice(0, 4).map(([key, value]) => `<div class="mini"><span>${{key}}</span><b>${{value}}</b></div>`).join('');
      return `<article class="room ${{room.tone}}" data-index="${{index}}">
        <h2>${{room.name}}</h2>
        <div class="modules">${{room.modules.join(' · ')}}</div>
        <div class="room-stats">${{stats}}</div>
      </article>`;
    }}

    function renderDetail(room) {{
      const rows = Object.entries(room.stats).map(([key, value]) => `<div class="detail-row"><span>${{key}}</span><b>${{value}}</b></div>`).join('');
      detail.innerHTML = `<h2>${{room.name}}</h2>
        <div class="modules">${{room.modules.join(' · ')}}</div>
        <div class="detail-list">${{rows}}</div>
        <div class="recommendation">${{room.recommendation}}</div>`;
    }}

    factory.innerHTML = data.rooms.map(renderRoom).join('');
    factory.querySelectorAll('.room').forEach((el) => {{
      el.addEventListener('click', () => {{
        factory.querySelectorAll('.room').forEach((room) => room.classList.remove('active'));
        el.classList.add('active');
        renderDetail(data.rooms[Number(el.dataset.index)]);
      }});
    }});
    renderDetail(data.rooms[0]);
    factory.querySelector('.room')?.classList.add('active');

    csvStats.innerHTML = data.csv_stats.map((row) => `<tr>
      <td>${{row.file}}</td>
      <td>${{row.rows}}</td>
      <td class="${{row.health}}">${{row.health}}</td>
    </tr>`).join('');
  </script>
</body>
</html>
"""


def _render_command_center_html(data: dict[str, object]) -> str:
    """Render the upgraded factory command center shell."""
    payload = _json_script(data)
    document = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>HomeBase Factory Command Center</title>
  <style>
    :root {
      --bg: #050812;
      --panel: rgba(13, 22, 35, 0.78);
      --text: #f1f7ff;
      --muted: #92a7bd;
      --line: rgba(95, 139, 171, 0.34);
      --accent: #34e7ff;
      --green: #48f2a0;
      --purple: #b28cff;
      --warn: #ffcf70;
      --hot: #ff7a90;
      --shadow: rgba(0, 0, 0, 0.35);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background:
        radial-gradient(circle at 14% 5%, rgba(52, 231, 255, 0.17), transparent 30%),
        radial-gradient(circle at 86% 8%, rgba(178, 140, 255, 0.15), transparent 28%),
        linear-gradient(145deg, #050812 0%, #09111d 52%, #04070d 100%);
      color: var(--text);
    }
    .shell { max-width: 1680px; margin: 0 auto; padding: 28px; }
    .topbar { display: flex; justify-content: space-between; gap: 18px; align-items: flex-start; margin-bottom: 18px; }
    h1 { margin: 0; font-size: 34px; letter-spacing: 0.04em; text-transform: uppercase; }
    .subtitle { margin: 8px 0 0; color: var(--muted); max-width: 900px; line-height: 1.55; }
    .stamp { color: var(--muted); font-size: 13px; text-align: right; }
    .kpis { display: grid; grid-template-columns: repeat(8, minmax(120px, 1fr)); gap: 12px; margin: 22px 0; }
    .kpi {
      background: linear-gradient(180deg, rgba(18, 32, 50, 0.86), rgba(9, 16, 29, 0.86));
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 14px;
      box-shadow: 0 16px 36px var(--shadow);
      backdrop-filter: blur(10px);
    }
    .kpi b { display: block; font-size: 23px; margin-bottom: 4px; overflow-wrap: anywhere; }
    .kpi span { color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: 0.09em; }
    .pipeline { margin: 20px 0; border: 1px solid var(--line); border-radius: 22px; padding: 16px; background: rgba(6, 12, 22, 0.72); box-shadow: 0 18px 46px var(--shadow); }
    .pipeline h2, .panel h2 { margin: 0 0 14px; font-size: 18px; text-transform: uppercase; letter-spacing: 0.05em; }
    .stages { display: grid; grid-template-columns: repeat(8, minmax(80px, 1fr)); gap: 8px; }
    .stage { position: relative; padding: 12px 10px; border: 1px solid rgba(95,139,171,0.32); border-radius: 14px; background: rgba(13,22,35,0.74); min-height: 78px; }
    .stage:not(:last-child)::after { content: "→"; position: absolute; right: -10px; top: 30px; color: var(--accent); z-index: 3; }
    .stage.bottleneck { border-color: var(--warn); box-shadow: 0 0 22px rgba(255,207,112,0.14); }
    .stage.active { background: rgba(19, 36, 55, 0.88); }
    .stage span { display: block; color: var(--muted); font-size: 10px; letter-spacing: 0.08em; }
    .stage b { display: block; font-size: 21px; margin-top: 6px; }
    .bar { height: 6px; background: rgba(143,166,184,0.18); border-radius: 999px; overflow: hidden; margin-top: 8px; }
    .bar div { height: 100%; background: linear-gradient(90deg, var(--accent), var(--green)); border-radius: 999px; }
    .layout { display: grid; grid-template-columns: minmax(780px, 1.45fr) minmax(360px, 0.7fr); gap: 20px; align-items: start; }
    .factory-floor {
      position: relative;
      min-height: 900px;
      border: 1px solid var(--line);
      border-radius: 28px;
      padding: 24px;
      background: rgba(6, 12, 22, 0.72);
      box-shadow: inset 0 0 60px rgba(52, 231, 255, 0.04), 0 18px 60px var(--shadow);
      overflow: hidden;
    }
    .factory-floor::before {
      content: "";
      position: absolute;
      inset: 70px 12% 120px;
      background:
        linear-gradient(90deg, transparent 0 31%, rgba(52, 231, 255, 0.26) 31.3% 31.7%, transparent 32%),
        linear-gradient(90deg, transparent 0 68%, rgba(52, 231, 255, 0.26) 68.3% 68.7%, transparent 69%),
        linear-gradient(180deg, transparent 0 21%, rgba(52, 231, 255, 0.22) 21.3% 21.7%, transparent 22%),
        linear-gradient(180deg, transparent 0 49%, rgba(52, 231, 255, 0.22) 49.3% 49.7%, transparent 50%),
        linear-gradient(180deg, transparent 0 72%, rgba(52, 231, 255, 0.22) 72.3% 72.7%, transparent 73%);
      pointer-events: none;
    }
    .factory-floor::after {
      content: "";
      position: absolute;
      left: 50%;
      top: 92px;
      bottom: 92px;
      width: 2px;
      background: linear-gradient(180deg, transparent, rgba(52,231,255,0.72), transparent);
      animation: flowPulse 4s ease-in-out infinite;
    }
    @keyframes flowPulse { 0%, 100% { opacity: 0.35; } 50% { opacity: 1; } }
    .room {
      position: absolute;
      width: 28%;
      min-height: 132px;
      padding: 16px;
      border: 1px solid var(--line);
      border-radius: 20px;
      background: linear-gradient(180deg, rgba(18, 31, 49, 0.82), rgba(8, 14, 26, 0.88));
      box-shadow: 0 18px 46px var(--shadow);
      backdrop-filter: blur(14px);
      cursor: pointer;
      transition: transform 160ms ease, border-color 160ms ease, box-shadow 160ms ease;
      z-index: 2;
    }
    .room:hover, .room.active { transform: translateY(-3px); border-color: var(--accent); box-shadow: 0 0 28px rgba(52, 231, 255, 0.18), 0 18px 46px var(--shadow); }
    .room.founder { left: 36%; top: 24px; }
    .room.generation { left: 4%; top: 238px; }
    .room.studio { left: 36%; top: 238px; }
    .room.signals { right: 4%; top: 238px; }
    .room.workflow { left: 36%; top: 455px; }
    .room.storage { left: 36%; top: 640px; }
    .room.market { left: 36%; top: 785px; }
    .status-dot { position: absolute; right: 14px; top: 14px; width: 12px; height: 12px; border-radius: 50%; animation: statusPulse 2.4s ease-in-out infinite; }
    .healthy .status-dot { background: var(--green); box-shadow: 0 0 18px var(--green); }
    .warning .status-dot { background: var(--warn); box-shadow: 0 0 18px var(--warn); }
    .danger .status-dot { background: var(--hot); box-shadow: 0 0 18px var(--hot); }
    @keyframes statusPulse { 0%, 100% { transform: scale(0.86); opacity: 0.65; } 50% { transform: scale(1.08); opacity: 1; } }
    .room h2 { font-size: 15px; margin: 0 24px 10px 0; text-transform: uppercase; letter-spacing: 0.05em; }
    .modules { color: var(--muted); font-size: 11px; line-height: 1.45; margin-bottom: 12px; }
    .room-stats { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
    .mini { border-top: 1px solid rgba(143, 166, 184, 0.2); padding-top: 7px; }
    .mini span { color: var(--muted); display: block; font-size: 10px; text-transform: uppercase; letter-spacing: 0.06em; }
    .mini b { font-size: 13px; overflow-wrap: anywhere; }
    .side { display: grid; gap: 16px; }
    .panel {
      border: 1px solid var(--line);
      border-radius: 22px;
      background: linear-gradient(180deg, rgba(17, 29, 47, 0.82), rgba(7, 13, 24, 0.88));
      padding: 18px;
      box-shadow: 0 18px 46px var(--shadow);
      backdrop-filter: blur(14px);
    }
    .recommendation { color: var(--accent); line-height: 1.5; margin: 14px 0; }
    .detail-list { display: grid; gap: 10px; }
    .detail-row { display: flex; justify-content: space-between; gap: 12px; border-bottom: 1px solid rgba(143,166,184,0.16); padding-bottom: 8px; }
    .detail-row span { color: var(--muted); }
    .detail-row b { text-align: right; overflow-wrap: anywhere; }
    .status-row { display: grid; grid-template-columns: repeat(4, minmax(140px, 1fr)); gap: 12px; margin: 20px 0; }
    .status-chip { border: 1px solid rgba(95,139,171,0.24); border-radius: 18px; padding: 14px 16px; background: rgba(12,20,32,0.88); box-shadow: inset 0 0 20px rgba(0,0,0,0.15); }
    .status-chip span { display: block; color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 6px; }
    .status-chip b { font-size: 20px; line-height: 1.2; }
    .status-chip em { font-size: 12px; color: var(--accent); }
    .market-grid, .listing-grid, .product-grid { display: grid; gap: 12px; }
    .market-card, .listing-card, .product-card { position: relative; border: 1px solid rgba(95,139,171,0.25); border-radius: 18px; padding: 16px; background: rgba(6,12,22,0.78); cursor: pointer; transition: transform 160ms ease, border-color 160ms ease, box-shadow 160ms ease; }
    .market-card:hover, .listing-card:hover, .product-card:hover { transform: translateY(-2px); border-color: var(--accent); box-shadow: 0 0 30px rgba(62,231,196,0.18); }
    .market-card span, .listing-card span, .product-card span { color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; }
    .market-card b, .listing-card b, .product-card b { display: block; margin: 8px 0; font-size: 17px; }
    .product-card .badge { display: inline-block; margin-top: 10px; padding: 4px 10px; border-radius: 999px; font-size: 11px; letter-spacing: 0.08em; }
    .product-card .badge.low { background: rgba(62,231,196,0.14); color: var(--green); }
    .product-card .badge.medium { background: rgba(255,207,112,0.14); color: var(--warn); }
    .product-card .badge.high { background: rgba(255,122,144,0.14); color: var(--hot); }
    .product-card .progress { height: 8px; border-radius: 999px; background: rgba(143,166,184,0.18); overflow: hidden; margin-top: 10px; }
    .product-card .progress > div { height: 100%; border-radius: 999px; background: linear-gradient(90deg, var(--accent), var(--green)); }
    .product-card.expanded { transform: scale(1.02); border-color: var(--accent); box-shadow: 0 0 26px rgba(62,231,196,0.24); }
    .money-path { display: flex; flex-wrap: wrap; gap: 10px; margin: 16px 0 0; }
    .path-node { flex: 1 1 110px; min-width: 110px; padding: 12px; border-radius: 16px; border: 1px solid rgba(95,139,171,0.18); background: rgba(7,13,24,0.68); text-align: center; }
    .path-node span { color: var(--muted); display: block; font-size: 10px; margin-bottom: 6px; }
    .path-node b { font-size: 14px; }
    .pulse { animation: pulseGlow 2.6s ease-in-out infinite; }
    .pulse-soft { animation-duration: 3.4s; }
    @keyframes pulseGlow { 0%, 100% { box-shadow: 0 0 8px rgba(62,231,196,0.08); } 50% { box-shadow: 0 0 22px rgba(62,231,196,0.22); } }
    .tooltip { position: absolute; z-index: 10; left: 50%; transform: translateX(-50%); bottom: calc(100% + 10px); min-width: 180px; padding: 10px 12px; border-radius: 14px; background: rgba(9,16,24,0.95); color: var(--text); font-size: 12px; box-shadow: 0 16px 34px rgba(0,0,0,0.35); display: none; }
    .room.expanded { transform: scale(1.02); }
    .room-icon { margin-right: 8px; }
    .stage-pill { display: inline-flex; align-items: center; gap: 6px; background: rgba(62,231,196,0.12); color: var(--accent); border-radius: 999px; padding: 4px 10px; font-size: 11px; }
    .stage-filters { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 12px; }
    .stage-filter { border: 1px solid rgba(95,139,171,0.22); border-radius: 999px; padding: 8px 12px; background: rgba(7,13,24,0.72); color: var(--muted); cursor: pointer; transition: background 140ms ease, color 140ms ease; }
    .stage-filter.active { background: rgba(62,231,196,0.14); color: var(--accent); }
    @media (max-width: 1180px) {
      .layout { grid-template-columns: 1fr; }
      .factory-floor { min-height: auto; display: grid; gap: 12px; }
      .factory-floor::before, .factory-floor::after { display: none; }
      .room { position: relative; inset: auto !important; width: 100%; }
      .kpis { grid-template-columns: repeat(2, minmax(120px, 1fr)); }
      .stages { grid-template-columns: repeat(2, minmax(120px, 1fr)); }
      .stage::after { display: none; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <header class="topbar">
      <div>
        <h1>HomeBase Factory Command Center</h1>
        <p class="subtitle">A local visual shell over the real AI Factory OS. It reads CSV memory and module outputs only. No uploads, no API calls, no servers, no background workers.</p>
      </div>
      <div class="stamp">Generated<br><span id="generatedAt"></span></div>
    </header>
    <section class="kpis" id="summary"></section>
    <section class="status-row" id="topStatus"></section>
    <section class="status-row" id="etsySync"></section>
    <section class="status-row" id="recommendationPanels"></section>
    <section class="pipeline">
      <h2>Product Lifecycle Pipeline</h2>
      <div class="stages" id="pipeline"></div>
      <div class="money-path" id="moneyFlow"></div>
    </section>
    <main class="layout">
      <section class="factory-floor" id="factory"></section>
      <aside class="side">
        <section class="panel" id="detail"></section>
        <section class="panel"><h2>Founder Execution Mode</h2><div id="execution"></div></section>
        <section class="panel"><h2>Signal Heatmap</h2><div class="heat-grid" id="heatmap"></div></section>
        <section class="panel"><h2>Market Terminals</h2><div class="market-grid" id="marketPanels"></div></section>
        <section class="panel"><h2>Market Output Terminals</h2><div class="dock-grid" id="docks"></div></section>
        <section class="panel"><h2>Live Listing Preview</h2><div class="listing-grid" id="listingPreviews"></div></section>
        <section class="panel"><h2>Ready-to-Work Queue</h2><div class="detail-list" id="readinessQueue"></div></section>
        <section class="panel"><h2>Recent Experiment Timeline</h2><div class="detail-list" id="experimentTimeline"></div></section>
        <section class="panel"><h2>Product Cards</h2><div class="stage-filters" id="stageFilters"></div><div class="product-grid" id="productCards"></div></section>
        <section class="panel"><h2>Memory Vault</h2><div class="memory-grid" id="csvStats"></div></section>
        <section class="ticker"><span>Explicit execution only · Use the CLI for readiness checks, metric imports, listing exports, and weekly reviews · The map is visual awareness, not automation · </span></section>
      </aside>
    </main>
  </div>
  <script id="factory-data" type="application/json">__FACTORY_DATA__</script>
  <script>
    const data = JSON.parse(document.getElementById('factory-data').textContent);
    const factory = document.getElementById('factory');
    const detail = document.getElementById('detail');
    const summary = document.getElementById('summary');
    const topStatus = document.getElementById('topStatus');
    const etsySync = document.getElementById('etsySync');
    const recommendationPanels = document.getElementById('recommendationPanels');
    const pipeline = document.getElementById('pipeline');
    const heatmap = document.getElementById('heatmap');
    const execution = document.getElementById('execution');
    const docks = document.getElementById('docks');
    const csvStats = document.getElementById('csvStats');
    document.getElementById('generatedAt').textContent = data.generated_at;

    const summaryItems = [
      ['Total Products', data.summary.products],
      ['Active Listings', data.summary.active_listings],
      ['Estimated Revenue', '$' + data.summary.revenue],
      ['Validated', data.summary.validation_count],
      ['Top Niche', data.summary.top_niche],
      ['Op Score', data.operational_score + '/100'],
      ['Signal Strength', data.signal_strength_progress + '%'],
      ['Listing Readiness', data.listing_readiness_progress + '%'],
    ];
    summary.innerHTML = summaryItems.map(([label, value]) => '<div class="kpi"><b>' + value + '</b><span>' + label + '</span></div>').join('');
    topStatus.innerHTML = [
      ['Factory Status', data.factory_status],
      ['Scale Readiness', data.scale_readiness],
      ['Current Focus', data.current_focus],
      ['Top Action', data.top_action],
    ].map(([label, value]) => '<div class="status-chip"><span>' + label + '</span><b>' + value + '</b></div>').join('');

    etsySync.innerHTML = [
      ['Imported Etsy Listings', data.etsy_sync.imported_etsy_listings],
      ['Active Etsy Listings', data.etsy_sync.imported_active_etsy],
      ['Imported Favorites', data.etsy_sync.imported_favorites],
      ['Imported Orders', data.etsy_sync.imported_orders],
      ['Imported Revenue', '$' + data.etsy_sync.imported_revenue],
      ['Top Viewed', data.etsy_sync.top_viewed_listing],
      ['Top Favorited', data.etsy_sync.top_favorited_listing],
      ['Top Converting', data.etsy_sync.top_converting_listing],
    ].map(([label, value]) => '<div class="status-chip"><span>' + label + '</span><b>' + value + '</b></div>').join('');

    recommendationPanels.innerHTML = [
      ['Most Likely Next Sale', data.etsy_sync.most_likely_next_sale],
      ['Weakest Listing', data.listing_health.top_weakest.length ? data.listing_health.top_weakest[0].listing_id : 'none yet'],
      ['Highest Potential Listing', data.recommendations.listing_to_duplicate],
      ['Recommended Action Today', data.recommendations.best_emotional_hook],
    ].map(([label, value]) => '<div class="status-chip"><span>' + label + '</span><b>' + value + '</b></div>').join('');

    const roomIcons = {
      founder: '🧭',
      generation: '⚙️',
      studio: '🎨',
      signals: '📡',
      workflow: '🔧',
      storage: '🗄️',
      market: '💰',
    };

    function renderRoom(room, index) {
      const stats = Object.entries(room.stats).slice(0, 4).map(([key, value]) => '<div class="mini"><span>' + key + '</span><b>' + value + '</b></div>').join('');
      const icon = roomIcons[room.id] || '🔹';
      return '<article class="room ' + room.id + ' ' + room.tone + '" data-index="' + index + '"><div class="status-dot"></div><h2><span class="room-icon">' + icon + '</span>' + room.name + '</h2><div class="modules">' + room.modules.join(' · ') + '</div><div class="room-stats">' + stats + '</div></article>';
    }

    function renderDetail(room) {
      const merged = Object.assign({}, room.stats, room.details || {});
      const rows = Object.entries(merged).map(([key, value]) => {
        const rendered = Array.isArray(value) ? value.map(item => typeof item === 'object' ? JSON.stringify(item) : item).join('<br>') : value;
        return '<div class="detail-row"><span>' + key + '</span><b>' + rendered + '</b></div>';
      }).join('');
      detail.innerHTML = '<h2>' + room.name + '</h2><div class="modules">' + room.modules.join(' · ') + '</div><div class="detail-list">' + rows + '</div><div class="recommendation">' + room.recommendation + '</div>';
    }

    function renderMarketPanels(panels) {
      return panels.map(panel => '<div class="market-card pulse-soft"><span>' + panel.emoji + ' ' + panel.name + '</span><b>' + panel.status + '</b><div>' + panel.count + ' items</div><div class="progress"><div style="width:' + Math.max(8, panel.signal) + '%"></div></div><span>' + (panel.revenue ? '$' + panel.revenue : 'no estimate') + '</span></div>').join('');
    }

    function renderMoneyFlow(flow) {
      return flow.map(node => '<div class="path-node"><span>' + node.status + '</span><b>' + node.step + '</b></div>').join('');
    }

    function renderListingPreviews(previews) {
      if (!previews.length) {
        return '<div class="listing-card"><span>No Listings Imported Yet</span><b>Awaiting first listing metrics</b><div class="progress"><div style="width:6%"></div></div></div>';
      }
      return previews.map(item => '<div class="listing-card pulse"><span>' + item.product_title + '</span><b>' + item.listing_id + '</b><div>Views: ' + item.views + ' · Fav: ' + item.favorites + ' · Orders: ' + item.orders + '</div><div class="progress"><div style="width:' + Math.max(8, Math.min(100, item.conversion_rate * 100)) + '%"></div></div></div>').join('');
    }

    function renderProductCards(cards) {
      if (!cards.length) {
        return '<div class="product-card"><span>Waiting for First Validation</span><b>No product cards yet</b><div class="badge low">Awaiting signal</div></div>';
      }
      return cards.map(card => '<div class="product-card" title="' + card.top_weakness + '"><span>' + card.niche + '</span><b>' + card.title + '</b><div>Stage: <span class="stage-pill">' + card.stage + '</span></div><div>Thumbnail: ' + card.thumbnail_style + '</div><div class="badge ' + card.duplicate_risk + '">dup risk: ' + card.duplicate_risk + '</div><div class="progress"><div style="width:' + Math.max(8, card.signal_strength) + '%"></div></div></div>').join('');
    }

    function renderExperimentTimeline(events) {
      if (!events.length) {
        return '<div class="detail-row"><span>Awaiting Market Signal</span><b>No experiments logged</b></div>';
      }
      return events.map(event => '<div class="detail-row"><span>' + event.changed_at + ' · ' + event.product_title + '</span><b>' + event.change_type + '</b><div>' + event.metrics + '</div></div>').join('');
    }

    function renderReadinessQueue(queue) {
      return Object.entries(queue).map(([key, items]) => '<div class="detail-row"><span>' + key.replace(/_/g, ' ') + '</span><b>' + (items.length ? items.join(', ') : 'none') + '</b></div>').join('');
    }

    factory.innerHTML = data.rooms.map(renderRoom).join('');
    factory.querySelectorAll('.room').forEach((el) => {
      el.addEventListener('click', () => {
        const already = el.classList.contains('active');
        factory.querySelectorAll('.room').forEach((room) => room.classList.remove('active', 'expanded'));
        el.classList.toggle('active', !already);
        el.classList.toggle('expanded', already);
        renderDetail(data.rooms[Number(el.dataset.index)]);
      });
    });
    renderDetail(data.rooms[0]);
    factory.querySelector('.room')?.classList.add('active');

    pipeline.innerHTML = data.pipeline.map(stage => '<div class="stage ' + (stage.active ? 'active ' : '') + (stage.bottleneck ? 'bottleneck' : '') + '"><span>' + stage.label + '</span><b>' + stage.count + '</b><div class="bar"><div style="width:' + Math.max(8, stage.percent) + '%"></div></div></div>').join('');
    heatmap.innerHTML = data.signal_heatmap.map(item => '<div class="heat"><span>' + item.label + '</span><b>' + item.value + '</b><div class="bar"><div style="width:' + Math.max(5, item.score) + '%"></div></div></div>').join('');
    execution.innerHTML = '<div class="recommendation">' + data.execution_mode.highest_leverage_fix + '</div>' + data.execution_mode.next_actions.map(action => '<div class="detail-row"><span>Action</span><b>' + action + '</b></div>').join('') + '<div class="detail-row"><span>Bottleneck</span><b>' + data.execution_mode.biggest_bottleneck + '</b></div>';
    docks.innerHTML = data.market_outputs.map(item => '<div class="dock"><span>' + item.status + '</span><b>' + item.name + '</b><div>' + item.count + ' ' + item.metric + '</div></div>').join('');
    document.getElementById('marketPanels').innerHTML = renderMarketPanels(data.market_panels);
    document.getElementById('moneyFlow').innerHTML = renderMoneyFlow(data.money_flow);
    document.getElementById('listingPreviews').innerHTML = renderListingPreviews(data.listing_previews);
    document.getElementById('productCards').innerHTML = renderProductCards(data.product_cards);
    document.querySelectorAll('.product-card').forEach(card => {
      card.addEventListener('click', () => card.classList.toggle('expanded'));
    });
    const stageFilters = document.getElementById('stageFilters');
    const stages = data.pipeline.map(stage => stage.label);
    stageFilters.innerHTML = stages.map(stageName => '<div class="stage-filter" data-stage="' + stageName + '">' + stageName + '</div>').join('');
    stageFilters.querySelectorAll('.stage-filter').forEach(button => {
      button.addEventListener('click', () => {
        stageFilters.querySelectorAll('.stage-filter').forEach(btn => btn.classList.remove('active'));
        button.classList.add('active');
        const selected = button.dataset.stage;
        document.getElementById('productCards').innerHTML = renderProductCards(data.product_cards.filter(card => card.stage === selected || selected === 'IDEATION' && !card.stage));
      });
    });
    document.getElementById('experimentTimeline').innerHTML = renderExperimentTimeline(data.experiment_timeline);
    document.getElementById('readinessQueue').innerHTML = renderReadinessQueue(data.readiness_queue);
    csvStats.innerHTML = data.csv_stats.map(row => '<div class="node"><span>' + row.health + '</span><b>' + row.file + '</b><div>' + row.rows + ' rows</div></div>').join('');
  </script>
</body>
</html>
"""
    return document.replace("__FACTORY_DATA__", payload)


def build_factory_map(output_path: Path | None = None) -> dict[str, object]:
    """Write the static factory map HTML and return build metadata."""
    data = collect_factory_map_data()
    output_path = output_path or FACTORY_MAP_HTML
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_render_command_center_html(data), encoding="utf-8")
    return {
        "output_path": str(output_path),
        "rooms_detected": [room["name"] for room in data["rooms"]],
        "csv_stats_loaded": data["csv_stats"],
        "summary": data["summary"],
        "status": "ready",
    }


if __name__ == "__main__":
    result = build_factory_map()
    print(result["output_path"])
