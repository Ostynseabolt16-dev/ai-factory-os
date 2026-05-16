"""Etsy listing text — LLM-backed when OPENAI_API_KEY is set."""

from ai_factory.listings.listing_llm import generate_etsy_listing_from_idea


def placeholder_listing_payload() -> dict:
    """Empty shells for tests or offline defaults."""
    return {
        "title": "",
        "description": "",
        "tags": [],
    }


def draft_listing_from_idea(idea: str) -> dict:
    """Same listing generator used by `python main.py` (calls OpenAI Chat)."""
    return generate_etsy_listing_from_idea(idea)
