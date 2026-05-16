"""Etsy listing copy, titles, tags, and future API integration."""

# TODO: Etsy Open API v3 when you're ready for automation

from ai_factory.listings.etsy_copy import (
    draft_listing_from_idea,
    placeholder_listing_payload,
)
from ai_factory.listings.listing_llm import generate_etsy_listing_from_idea
from ai_factory.listings.listing_tracker import (
    create_listing_record,
    generate_listing_report,
    mark_listing_sold,
    pause_listing,
    read_listings,
    remove_listing,
    update_listing_metrics,
    update_thumbnail_test,
)
from ai_factory.listings.etsy_readiness import evaluate_etsy_readiness, generate_readiness_report
from ai_factory.listings.etsy_metrics_importer import (
    bulk_update_metrics,
    compare_listing_performance,
    import_listing_metrics,
)
from ai_factory.listings.etsy_seo_optimizer import (
    analyze_tags,
    analyze_title,
    score_seo_strength,
    suggest_keyword_expansion,
)
from ai_factory.listings.listing_change_history import (
    read_listing_change_history,
    record_listing_change,
    summarize_listing_changes,
)
from ai_factory.listings.listing_packager import export_listing_package

__all__ = [
    "create_listing_record",
    "evaluate_etsy_readiness",
    "export_listing_package",
    "bulk_update_metrics",
    "compare_listing_performance",
    "generate_readiness_report",
    "draft_listing_from_idea",
    "generate_listing_report",
    "generate_etsy_listing_from_idea",
    "import_listing_metrics",
    "mark_listing_sold",
    "pause_listing",
    "placeholder_listing_payload",
    "read_listings",
    "read_listing_change_history",
    "record_listing_change",
    "remove_listing",
    "analyze_tags",
    "analyze_title",
    "score_seo_strength",
    "summarize_listing_changes",
    "suggest_keyword_expansion",
    "update_listing_metrics",
    "update_thumbnail_test",
]

