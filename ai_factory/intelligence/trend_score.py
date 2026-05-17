"""Trend and listing intelligence for AI Factory OS.

This module supports manual trend CSV imports, normalized scoring, product
recommendations, and lightweight product clustering without relying on APIs.
"""

from __future__ import annotations

import csv
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from ai_factory.config import PROJECT_ROOT, TREND_DATA_CSV
from ai_factory.products.product_manager import read_products, update_product_fields

TREND_DATA_COLUMNS = [
    "keyword",
    "niche",
    "search_volume",
    "trend_velocity",
    "source",
    "raw_score",
    "normalized_score",
    "imported_at",
]

TREND_DEFAULT_SOURCE = "manual"


def _now() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def _ensure_trend_csv() -> None:
    if not TREND_DATA_CSV.exists():
        TREND_DATA_CSV.parent.mkdir(parents=True, exist_ok=True)
        with TREND_DATA_CSV.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=TREND_DATA_COLUMNS)
            writer.writeheader()


def _parse_float(value: str | int | float | None, default: float = 0.0) -> float:
    try:
        return float(str(value or "").replace(",", "").strip())
    except (TypeError, ValueError):
        return default


def _normalize(values: list[float]) -> list[float]:
    if not values:
        return []
    minimum = min(values)
    maximum = max(values)
    if math.isclose(minimum, maximum):
        return [100.0 for _ in values]
    return [round((value - minimum) / (maximum - minimum) * 100.0, 2) for value in values]


def _read_trend_data() -> list[dict[str, str]]:
    _ensure_trend_csv()
    with TREND_DATA_CSV.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_trend_data(rows: list[dict[str, str]]) -> None:
    _ensure_trend_csv()
    with TREND_DATA_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=TREND_DATA_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in TREND_DATA_COLUMNS})


def load_trend_data() -> list[dict[str, str]]:
    return _read_trend_data()


def import_trend_csv(csv_path: str | Path) -> dict[str, Any]:
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Trend CSV not found: {csv_path}")

    rows: list[dict[str, str]] = []
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for raw in reader:
            keyword = (raw.get("keyword") or raw.get("term") or "").strip().lower()
            niche = (raw.get("niche") or raw.get("category") or "").strip().lower()
            search_volume = _parse_float(raw.get("search_volume") or raw.get("volume") or raw.get("popularity"))
            trend_velocity = _parse_float(raw.get("trend_velocity") or raw.get("velocity") or raw.get("growth"))
            if not keyword:
                continue
            rows.append(
                {
                    "keyword": keyword,
                    "niche": niche,
                    "search_volume": str(search_volume),
                    "trend_velocity": str(trend_velocity),
                    "source": (raw.get("source") or TREND_DEFAULT_SOURCE).strip(),
                    "raw_score": "",
                    "normalized_score": "",
                    "imported_at": _now(),
                }
            )

    if not rows:
        raise RuntimeError("No valid trend rows found in CSV.")

    raw_scores = [_parse_float(row["search_volume"]) * 0.7 + _parse_float(row["trend_velocity"]) * 0.3 for row in rows]
    normalized = _normalize(raw_scores)
    for row, raw_score, norm in zip(rows, raw_scores, normalized):
        row["raw_score"] = str(round(raw_score, 2))
        row["normalized_score"] = str(round(norm, 2))

    _write_trend_data(rows)
    return {
        "imported": len(rows),
        "trend_file": str(TREND_DATA_CSV),
        "top_trends": sorted(rows, key=lambda item: _parse_float(item["normalized_score"]), reverse=True)[:5],
    }


def _normalize_keyword(value: str) -> str:
    return "".join(ch if ch.isalnum() else " " for ch in (value or "").lower()).strip()


def _keywords_from_product(product: dict[str, str]) -> set[str]:
    keywords: set[str] = set()
    for source in [product.get("niche"), product.get("title"), product.get("tags")]:
        if not source:
            continue
        for token in _normalize_keyword(str(source)).split():
            if len(token) >= 3:
                keywords.add(token)
    return keywords


def _matching_trend_rows(product: dict[str, str], trends: list[dict[str, str]] | None = None) -> list[dict[str, str]]:
    trends = trends or load_trend_data()
    product_keywords = _keywords_from_product(product)
    matches: list[dict[str, str]] = []
    for row in trends:
        keyword = (row.get("keyword") or "").strip().lower()
        niche = (row.get("niche") or "").strip().lower()
        if keyword and keyword in product_keywords:
            matches.append(row)
        elif niche and niche in product_keywords:
            matches.append(row)
    return matches


def calculate_product_trend_score(product: dict[str, str], trends: list[dict[str, str]] | None = None) -> int:
    trends = trends or load_trend_data()
    matches = _matching_trend_rows(product, trends)
    if not matches:
        return 0
    base = sum(_parse_float(row["normalized_score"]) for row in matches) / len(matches)
    quality = float(product.get("quality_score") or 0)
    completeness = float(product.get("listing_completeness_score") or 0)
    score = min(100.0, base * 0.7 + min(100.0, quality * 10) * 0.15 + completeness * 0.15)
    return int(round(score))


def score_title_quality(product: dict[str, str]) -> int:
    title = (product.get("title") or "").strip()
    words = [word for word in _normalize_keyword(title).split() if word]
    tags = {tag.lower() for tag in (product.get("tags") or "").split("|") if tag.strip()}
    score = 20
    score += min(40, len(words) * 4)
    score += 20 if any(word in tags for word in words) else 0
    score += 10 if product.get("niche") and product.get("niche").lower() in title.lower() else 0
    if len(words) < 4:
        score -= 15
    if len(words) > 18:
        score -= 10
    return max(0, min(100, score))


def score_tag_quality(product: dict[str, str]) -> int:
    tags = [tag.strip().lower() for tag in (product.get("tags") or "").split("|") if tag.strip()]
    unique = len(set(tags))
    count = len(tags)
    score = 0
    if count == 0:
        return 0
    if 5 <= count <= 13:
        score += 40
    else:
        score += max(0, 20 - abs(count - 9) * 2)
    score += min(30, unique * 5)
    if count >= 5 and unique >= count:
        score += 30
    return max(0, min(100, score))


def score_listing_completeness(product: dict[str, str]) -> int:
    checks = 0
    total = 5
    checks += 1 if (product.get("title") or "").strip() else 0
    checks += 1 if (product.get("tags") or "").strip() else 0
    checks += 1 if (product.get("description") or "").strip() else 0
    checks += 1 if (product.get("mockup_paths") or "").strip() else 0
    checks += 1 if product.get("status") in {"upload_ready", "uploaded", "listed", "sold"} else 0
    return int(round((checks / total) * 100))


def score_niche_confidence(product: dict[str, str], trends: list[dict[str, str]] | None = None) -> int:
    trends = trends or load_trend_data()
    niche = (product.get("niche") or "").strip().lower()
    if not niche:
        return 0
    niche_matches = [row for row in trends if (row.get("niche") or "").strip().lower() == niche]
    if niche_matches:
        return int(round(sum(_parse_float(row["normalized_score"]) for row in niche_matches) / len(niche_matches)))
    return int(round(score_listing_completeness(product) * 0.5 + score_title_quality(product) * 0.25))


def recommend_title_improvement(product: dict[str, str], trends: list[dict[str, str]] | None = None) -> list[str]:
    suggestions: list[str] = []
    title = (product.get("title") or "").strip()
    if not title:
        suggestions.append("Add a descriptive title with niche and benefit language.")
    if product.get("niche") and product.get("niche").lower() not in title.lower():
        suggestions.append("Include the niche term in the title.")
    if len(_normalize_keyword(title).split()) < 4:
        suggestions.append("Expand the title with more relevant keywords.")
    trends = trends or load_trend_data()
    keyword_matches = [row["keyword"] for row in _matching_trend_rows(product, trends)][:3]
    if keyword_matches:
        suggestions.append(f"Consider adding trending keywords: {', '.join(keyword_matches)}.")
    return suggestions


def recommend_tag_improvement(product: dict[str, str], trends: list[dict[str, str]] | None = None) -> list[str]:
    suggestions: list[str] = []
    tags = [tag.strip() for tag in (product.get("tags") or "").split("|") if tag.strip()]
    if len(tags) < 5:
        suggestions.append("Add at least 5 tags for better discoverability.")
    if len(set(tags)) < len(tags):
        suggestions.append("Remove duplicate tags and keep each tag unique.")
    trends = trends or load_trend_data()
    product_keywords = _keywords_from_product(product)
    missing = [row["keyword"] for row in trends if row["keyword"] not in tags and row["keyword"] in product_keywords][:3]
    if missing:
        suggestions.append(f"Add relevant trending tags: {', '.join(missing)}.")
    return suggestions


def cluster_products_by_topic(products: list[dict[str, str]] | None = None, min_shared: int = 2) -> list[dict[str, Any]]:
    products = products or read_products()
    keywords = {product["id"]: _keywords_from_product(product) for product in products}
    clusters: list[dict[str, Any]] = []
    seen: set[str] = set()

    for product_id, product_keywords in keywords.items():
        if product_id in seen:
            continue
        cluster_ids = {product_id}
        shared_keywords: Counter[str] = Counter()
        for other_id, other_keywords in keywords.items():
            if other_id == product_id:
                continue
            overlap = product_keywords.intersection(other_keywords)
            if len(overlap) >= min_shared:
                cluster_ids.add(other_id)
                shared_keywords.update(overlap)
        if len(cluster_ids) > 1:
            seen.update(cluster_ids)
            clusters.append(
                {
                    "cluster_size": len(cluster_ids),
                    "product_ids": sorted(cluster_ids),
                    "shared_keywords": [keyword for keyword, _ in shared_keywords.most_common(5)],
                }
            )
    return sorted(clusters, key=lambda item: item["cluster_size"], reverse=True)


def detect_niche_saturation(products: list[dict[str, str]] | None = None, min_count: int = 4, quality_threshold: int = 3) -> list[dict[str, Any]]:
    products = products or read_products()
    niches: dict[str, list[dict[str, str]]] = defaultdict(list)
    for product in products:
        niche = (product.get("niche") or "unknown").strip().lower()
        niches[niche].append(product)

    saturated: list[dict[str, Any]] = []
    for niche, rows in niches.items():
        count = len(rows)
        quality_scores = [float(row.get("quality_score") or 0) for row in rows]
        avg_quality = sum(quality_scores) / max(1, len(quality_scores))
        if count >= min_count and avg_quality <= quality_threshold:
            saturated.append(
                {
                    "niche": niche,
                    "product_count": count,
                    "average_quality_score": round(avg_quality, 2),
                }
            )
    return sorted(saturated, key=lambda item: item["product_count"], reverse=True)


def recommend_higher_performing_niches(trends: list[dict[str, str]] | None = None, limit: int = 5) -> list[dict[str, Any]]:
    trends = trends or load_trend_data()
    by_niche: dict[str, list[float]] = defaultdict(list)
    for row in trends:
        niche = (row.get("niche") or "unknown").strip().lower()
        by_niche[niche].append(_parse_float(row.get("normalized_score")))

    recommendations = [
        {
            "niche": niche,
            "score": round(sum(values) / len(values), 2),
            "trend_terms": sorted({row.get("keyword") for row in trends if (row.get("niche") or "").strip().lower() == niche})[:5],
        }
        for niche, values in by_niche.items()
    ]
    return sorted(recommendations, key=lambda item: item["score"], reverse=True)[:limit]


def generate_product_intelligence(product: dict[str, str], trends: list[dict[str, str]] | None = None) -> dict[str, Any]:
    trends = trends or load_trend_data()
    trend_score = calculate_product_trend_score(product, trends)
    title_quality_score = score_title_quality(product)
    tag_quality_score = score_tag_quality(product)
    listing_completeness_score = score_listing_completeness(product)
    niche_confidence = score_niche_confidence(product, trends)

    return {
        "product_id": product.get("id", ""),
        "trend_score": trend_score,
        "title_quality_score": title_quality_score,
        "tag_quality_score": tag_quality_score,
        "listing_completeness_score": listing_completeness_score,
        "niche_confidence": niche_confidence,
        "trend_matches": _matching_trend_rows(product, trends)[:5],
        "title_suggestions": recommend_title_improvement(product, trends),
        "tag_suggestions": recommend_tag_improvement(product, trends),
        "listing_weaknesses": [
            reason
            for reason in [
                "title too short" if title_quality_score < 40 else "",
                "tag set too weak" if tag_quality_score < 40 else "",
                "listing incomplete" if listing_completeness_score < 60 else "",
                "niche confidence low" if niche_confidence < 40 else "",
            ]
            if reason
        ],
    }


def score_all_products(trends: list[dict[str, str]] | None = None) -> dict[str, int]:
    trends = trends or load_trend_data()
    products = read_products()
    updated = 0
    for product in products:
        intelligence = generate_product_intelligence(product, trends)
        updates = {
            "trend_score": intelligence["trend_score"],
            "title_quality_score": intelligence["title_quality_score"],
            "tag_quality_score": intelligence["tag_quality_score"],
            "listing_completeness_score": intelligence["listing_completeness_score"],
            "niche_confidence": intelligence["niche_confidence"],
        }
        update_product_fields(product["id"], updates)
        updated += 1
    return {"updated_products": updated, "total_products": len(products)}
