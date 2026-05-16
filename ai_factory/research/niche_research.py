"""Local niche research helpers for AI Factory OS.

No OpenAI calls happen here. Etsy is only contacted when one of these functions
is explicitly called, and results are saved locally for Founder Agent decisions.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
from urllib.parse import quote_plus

from ai_factory.config import PROJECT_ROOT
from ai_factory.research.etsy_trends import fetch_etsy_search_titles

NICHE_REPORT_CSV = PROJECT_ROOT / "niche_report.csv"

TREND_WORDS = {
    "aesthetic",
    "bold",
    "christian",
    "coquette",
    "cute",
    "funny",
    "gift",
    "goth",
    "kawaii",
    "meme",
    "minimalist",
    "mom",
    "nurse",
    "retro",
    "sarcastic",
    "teacher",
    "vintage",
}


def _etsy_search_url(keyword: str) -> str:
    query = quote_plus(f"{keyword} shirt")
    return f"https://www.etsy.com/search?q={query}"


def _trend_keywords_from_titles(titles: list[str]) -> list[str]:
    words: list[str] = []
    for title in titles:
        cleaned = title.lower().replace("-", " ").replace("|", " ")
        words.extend(word.strip(".,!?:;()[]\"'") for word in cleaned.split())

    counts = Counter(word for word in words if word in TREND_WORDS)
    return [word for word, _ in counts.most_common(8)]


def search_etsy_trends(keyword: str) -> dict[str, object]:
    """
    Search Etsy titles for a keyword and detect basic trend words.

    This is best-effort public HTML research. If Etsy changes its page layout,
    the function returns fewer signals rather than breaking the whole system.
    """
    keyword = keyword.strip()
    if not keyword:
        raise ValueError("Keyword must not be empty.")

    url = _etsy_search_url(keyword)
    titles = fetch_etsy_search_titles(url, limit=30)
    trend_keywords = _trend_keywords_from_titles(titles)

    return {
        "keyword": keyword,
        "url": url,
        "title_count": len(titles),
        "titles": titles,
        "trend_keywords": trend_keywords,
        "demand_score": min(10, len(titles) // 3 + len(trend_keywords)),
    }


def estimate_competition(keyword: str, titles: list[str] | None = None) -> dict[str, object]:
    """
    Estimate competition from how often the exact keyword appears in result titles.

    This is not a perfect market-size metric; it is a cheap first filter.
    """
    keyword = keyword.strip().lower()
    if not keyword:
        raise ValueError("Keyword must not be empty.")

    if titles is None:
        titles = search_etsy_trends(keyword)["titles"]  # type: ignore[index]

    exact_matches = sum(1 for title in titles if keyword in title.lower())

    if exact_matches >= 15:
        level = "high"
        score = 3
    elif exact_matches >= 6:
        level = "medium"
        score = 6
    else:
        level = "low"
        score = 9

    return {
        "keyword": keyword,
        "competition_level": level,
        "competition_score": score,
        "exact_matches": exact_matches,
    }


def score_niche(keyword: str) -> dict[str, object]:
    """
    Rank a niche using demand, competition, and trend indicators.

    Higher score is better. This favors high demand, lower competition, and
    recognizable Etsy trend words.
    """
    trend_data = search_etsy_trends(keyword)
    titles = trend_data["titles"]
    competition = estimate_competition(keyword, titles=titles)  # type: ignore[arg-type]

    demand_score = int(trend_data["demand_score"])
    competition_score = int(competition["competition_score"])
    trend_bonus = len(trend_data["trend_keywords"]) * 2  # type: ignore[arg-type]
    total_score = demand_score * 7 + competition_score * 3 + trend_bonus

    if total_score >= 85:
        recommendation = "prioritize"
    elif total_score >= 60:
        recommendation = "test small batch"
    else:
        recommendation = "skip for now"

    return {
        "keyword": keyword.strip(),
        "score": total_score,
        "demand_score": demand_score,
        "competition_level": competition["competition_level"],
        "competition_score": competition_score,
        "trend_keywords": ", ".join(trend_data["trend_keywords"]),  # type: ignore[arg-type]
        "recommendation": recommendation,
    }


def save_niche_report(
    keywords: list[str] | None = None,
    *,
    output_path: Path = NICHE_REPORT_CSV,
) -> list[dict[str, object]]:
    """
    Score niches and save a local CSV report.

    Pass explicit keywords from the Founder Agent or manual experiments. The
    default list is intentionally small to avoid heavy scraping.
    """
    keywords = keywords or ["nurse humor", "teacher gifts", "retro anxiety", "dog mom"]
    reports: list[dict[str, object]] = []

    for keyword in keywords:
        try:
            reports.append(score_niche(keyword))
        except Exception as exc:
            reports.append(
                {
                    "keyword": keyword,
                    "score": 0,
                    "demand_score": 0,
                    "competition_level": "unknown",
                    "competition_score": 0,
                    "trend_keywords": "",
                    "recommendation": f"research failed: {exc}",
                }
            )

    reports.sort(key=lambda row: int(row["score"]), reverse=True)

    fieldnames = [
        "keyword",
        "score",
        "demand_score",
        "competition_level",
        "competition_score",
        "trend_keywords",
        "recommendation",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(reports)

    return reports

