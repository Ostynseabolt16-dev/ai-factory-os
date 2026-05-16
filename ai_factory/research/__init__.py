"""Market research and trend scraping."""

from ai_factory.research.etsy_trends import fetch_etsy_search_titles
from ai_factory.research.niche_research import (
    estimate_competition,
    save_niche_report,
    score_niche,
    search_etsy_trends,
)
from ai_factory.research.etsy_listing_research import (
    generate_niche_research_summary,
    record_competitor_observation,
)

__all__ = [
    "estimate_competition",
    "fetch_etsy_search_titles",
    "generate_niche_research_summary",
    "record_competitor_observation",
    "save_niche_report",
    "score_niche",
    "search_etsy_trends",
]
