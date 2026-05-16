"""Quality gates and duplicate detection."""

from ai_factory.quality.duplicate_detector import (
    detect_duplicate_titles,
    detect_reused_tags,
    detect_similar_products,
    generate_duplicate_report,
)
from ai_factory.quality.quality_gate import (
    calculate_overall_quality,
    validate_design_quality,
    validate_listing_quality,
    validate_mockup_quality,
)

__all__ = [
    "calculate_overall_quality",
    "detect_duplicate_titles",
    "detect_reused_tags",
    "detect_similar_products",
    "generate_duplicate_report",
    "validate_design_quality",
    "validate_listing_quality",
    "validate_mockup_quality",
]
