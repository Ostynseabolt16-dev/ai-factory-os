"""
Contracts for external agents (Cursor, scheduled jobs, future SDK).

Keep side effects in small functions with explicit inputs/outputs so tools can call them safely.
"""

from ai_factory.agents.founder_agent import (
    business_recommendations,
    founder_dashboard,
    founder_inventory_report,
    founder_niche_recommendations,
    founder_task_report,
    generate_founder_recommendations,
    get_founder_metrics,
    print_founder_report,
    recommend_next_action,
    request_bulk_designs,
    schedule_founder_task,
    schedule_analytics_refresh,
    schedule_batch_generation,
    schedule_batch_mockups,
    schedule_batch_review,
    schedule_generate_designs,
    schedule_generate_listing,
    schedule_generate_mockups,
    schedule_niche_research,
    task_recommendations,
)
from ai_factory.agents.founder_intelligence import (
    generate_daily_focus,
    generate_growth_opportunities,
    generate_pipeline_bottlenecks,
    generate_quality_alerts,
    generate_risk_report,
)

__all__ = [
    "business_recommendations",
    "founder_dashboard",
    "founder_inventory_report",
    "founder_niche_recommendations",
    "founder_task_report",
    "generate_founder_recommendations",
    "generate_daily_focus",
    "generate_growth_opportunities",
    "generate_pipeline_bottlenecks",
    "generate_quality_alerts",
    "generate_risk_report",
    "get_founder_metrics",
    "print_founder_report",
    "recommend_next_action",
    "request_bulk_designs",
    "schedule_founder_task",
    "schedule_analytics_refresh",
    "schedule_batch_generation",
    "schedule_batch_mockups",
    "schedule_batch_review",
    "schedule_generate_designs",
    "schedule_generate_listing",
    "schedule_generate_mockups",
    "schedule_niche_research",
    "task_recommendations",
]

# TODO: add thin wrappers: generate_design(idea) -> path, draft_listing(idea) -> dict
# TODO: never embed API keys in prompts; always read from env via ai_factory.config
