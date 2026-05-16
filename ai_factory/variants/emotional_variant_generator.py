"""Generate structured emotional-theme product variants.

This module creates variant ideas only. It does not generate images, call AI,
or schedule work.
"""

from __future__ import annotations

EMOTIONAL_ANGLES = [
    "Social Battery Low",
    "Overthinking Club",
    "Emotionally Exhausted",
    "Avoiding People Professionally",
    "Tiny Panic Attack",
    "Introvert Recovery Mode",
    "Awkward But Trying",
    "Please Do Not Perceive Me",
]


def _tags_for_angle(angle: str, base_concept: str) -> list[str]:
    words = [word.lower() for word in angle.replace("-", " ").split() if word]
    tags = [
        f"{base_concept.lower()} sticker"[:20],
        "mental health"[:20],
        "kawaii sticker"[:20],
        "planner sticker"[:20],
        "anxiety sticker"[:20],
        "laptop decal"[:20],
    ]
    for word in words:
        tags.append(f"{word} sticker"[:20])
        tags.append(f"{word} gift"[:20])
    unique: list[str] = []
    for tag in tags:
        cleaned = tag.strip()
        if cleaned and cleaned not in unique:
            unique.append(cleaned)
        if len(unique) >= 13:
            break
    return unique


def generate_emotional_variants(base_concept: str, *, limit: int = 6) -> list[dict[str, object]]:
    """Create structured variant ideas for a validated emotional concept."""
    base = (base_concept or "Social Anxiety").strip()
    variants = []
    for angle in EMOTIONAL_ANGLES[: max(1, limit)]:
        variants.append(
            {
                "base_concept": base,
                "variant_angle": angle,
                "title": f"{angle} Sticker Sheet - Cute {base} Kawaii Planner Stickers",
                "hook": f"For buyers who relate to {angle.lower()} moments and want cute, shareable stickers.",
                "tags": _tags_for_angle(angle, base),
                "experiment_idea": f"Test '{angle}' against the original '{base}' listing with the same mockup style.",
            }
        )
    return variants


def suggest_cluster_variants(base_concept: str, engagement_level: str = "promising") -> dict[str, object]:
    """Suggest nearby emotional variants only when a concept earns signal."""
    allowed = engagement_level in {"emerging", "promising", "validated", "scaling_candidate", "breakout_watch"}
    variants = generate_emotional_variants(base_concept, limit=3) if allowed else []
    return {
        "base_concept": base_concept,
        "engagement_level": engagement_level,
        "should_expand": allowed,
        "suggested_variants": variants,
        "rule": "Expand only into nearby emotional hooks after engagement appears.",
    }
