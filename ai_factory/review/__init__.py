"""Local product review heuristics."""

from ai_factory.review.review_engine import (
    calculate_review_score,
    review_product,
    suggest_improvements,
)
from ai_factory.review.design_improvement import analyze_design_weaknesses, suggest_design_improvements

__all__ = [
    "analyze_design_weaknesses",
    "calculate_review_score",
    "review_product",
    "suggest_design_improvements",
    "suggest_improvements",
]
