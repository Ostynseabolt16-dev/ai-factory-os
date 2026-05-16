"""Manual Etsy competitor observation tracker."""

from __future__ import annotations

import csv
import uuid

from ai_factory.config import PROJECT_ROOT
from ai_factory.tasks.task_models import now_iso

ETSY_RESEARCH_CSV = PROJECT_ROOT / "etsy_research.csv"
RESEARCH_COLUMNS = [
    "observation_id",
    "created_at",
    "niche",
    "competitor_title",
    "price_observation",
    "keyword_observation",
    "style_observation",
    "market_saturation_notes",
    "notes",
]


def _ensure() -> None:
    if not ETSY_RESEARCH_CSV.exists():
        with ETSY_RESEARCH_CSV.open("w", encoding="utf-8", newline="") as f:
            csv.DictWriter(f, fieldnames=RESEARCH_COLUMNS).writeheader()


def _read() -> list[dict[str, str]]:
    _ensure()
    with ETSY_RESEARCH_CSV.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def record_competitor_observation(
    *,
    niche: str,
    competitor_title: str = "",
    price_observation: str = "",
    keyword_observation: str = "",
    style_observation: str = "",
    market_saturation_notes: str = "",
    notes: str = "",
) -> str:
    """Record one manual competitor observation."""
    observation_id = str(uuid.uuid4())
    rows = _read()
    rows.append(
        {
            "observation_id": observation_id,
            "created_at": now_iso(),
            "niche": niche,
            "competitor_title": competitor_title,
            "price_observation": price_observation,
            "keyword_observation": keyword_observation,
            "style_observation": style_observation,
            "market_saturation_notes": market_saturation_notes,
            "notes": notes,
        }
    )
    with ETSY_RESEARCH_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=RESEARCH_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return observation_id


def generate_niche_research_summary(niche: str | None = None) -> dict[str, object]:
    rows = _read()
    if niche:
        rows = [row for row in rows if row.get("niche", "").lower() == niche.lower()]
    keywords: dict[str, int] = {}
    for row in rows:
        for word in (row.get("keyword_observation") or "").replace(",", " ").split():
            keywords[word.lower()] = keywords.get(word.lower(), 0) + 1
    return {"observation_count": len(rows), "top_keywords": sorted(keywords.items(), key=lambda item: item[1], reverse=True)[:10], "recent": rows[-5:]}

