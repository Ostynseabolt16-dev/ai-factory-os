"""Local listing preparation helpers.

No OpenAI calls here. These templates are intentionally simple so products can
move from reviewed -> upload_ready without paid API usage.
"""

from __future__ import annotations


FILLER_TAGS = [
    "graphic tee",
    "etsy gift",
    "pod shirt",
    "trendy tee",
    "unique shirt",
    "gift for her",
    "gift for him",
    "birthday gift",
    "casual shirt",
    "statement tee",
]


def _clean_words(value: str) -> list[str]:
    return [word.strip("-_ ").lower() for word in value.replace("_", " ").replace("|", " ").split() if word.strip("-_ ")]


def _parts(product: dict[str, str]) -> tuple[str, str, str]:
    niche = (product.get("niche") or product.get("idea") or "graphic").strip()
    filename = (product.get("filename") or "").lower()
    style = "retro" if "retro" in filename or "retro" in niche.lower() else "bold"
    angle = "funny" if "funny" in niche.lower() or "humor" in niche.lower() else "gift"
    return style, niche, angle


def _title_case_phrase(value: str) -> str:
    return " ".join(word.capitalize() for word in _clean_words(value))


def generate_title(product: dict[str, str]) -> str:
    """Generate an SEO-style Etsy title from local product fields."""
    style, niche, angle = _parts(product)
    niche_title = _title_case_phrase(niche)
    pieces = [
        f"{style.title()} {niche_title} Shirt",
        f"{angle.title()} Graphic Tee",
        "Unique Gift",
        "Print On Demand Design",
    ]
    title = " | ".join(dict.fromkeys(piece for piece in pieces if piece.strip()))
    return title[:140]


def generate_tags(product: dict[str, str]) -> str:
    """Generate pipe-separated Etsy-style tags from local product fields."""
    style, niche, angle = _parts(product)
    niche_words = _clean_words(niche)
    niche_phrase = " ".join(niche_words[:3]).strip()
    tags = [
        f"{style} shirt",
        f"{angle} shirt",
        f"{style} tee",
        f"{angle} gift",
        niche_phrase[:20] if niche_phrase else "",
        "graphic tee",
        "etsy gift",
        "unique shirt",
    ]
    for word in niche_words:
        tags.append(word[:20])
        tags.append(f"{word} shirt")
        tags.append(f"{word} gift")
    tags.extend(FILLER_TAGS)
    unique: list[str] = []
    for tag in tags:
        cleaned = " ".join(_clean_words(tag))[:20]
        if cleaned not in unique:
            unique.append(cleaned)
        if len(unique) >= 13:
            break
    while len(unique) < 13:
        fallback = FILLER_TAGS[len(unique) % len(FILLER_TAGS)]
        if fallback not in unique:
            unique.append(fallback)
    return "|".join(unique)


def generate_description(product: dict[str, str]) -> str:
    """Generate a short local Etsy description template."""
    style, niche, angle = _parts(product)
    return (
        f"This {style} {niche} design is made for buyers looking for a {angle} graphic tee "
        "with a clean, giftable look.\n\n"
        "Great for casual outfits, birthdays, holidays, niche communities, or print-on-demand testing. "
        "Review sizing, colors, and production details in your Etsy/Printify listing before publishing.\n\n"
        "Created as part of AI Factory OS and ready for manual review before upload."
    )


def score_listing_quality(product: dict[str, str]) -> dict[str, object]:
    """Score local listing metadata for manual upload readiness."""
    title = (product.get("title") or generate_title(product)).strip()
    tags_raw = (product.get("tags") or generate_tags(product)).strip()
    description = (product.get("description") or generate_description(product)).strip()
    tags = [tag.strip().lower() for tag in tags_raw.replace(",", "|").split("|") if tag.strip()]
    warnings: list[str] = []
    score = 0

    if 55 <= len(title) <= 140:
        score += 30
    else:
        warnings.append("title should be readable and under Etsy's 140 character limit")
        score += 10 if title else 0
    title_words = _clean_words(title)
    if len(set(title_words)) >= max(4, len(title_words) - 2):
        score += 10
    else:
        warnings.append("title repeats too many phrases")

    if len(tags) >= 13:
        score += 25
    else:
        warnings.append("listing should have 13 tags")
        score += min(20, len(tags) * 2)
    if len(set(tags)) == len(tags):
        score += 10
    else:
        warnings.append("tags include duplicates")
    if all(len(tag) <= 20 for tag in tags):
        score += 10
    else:
        warnings.append("some tags exceed Etsy's 20 character tag limit")

    if len(description) >= 180:
        score += 15
    else:
        warnings.append("description is too short for confident manual upload")

    return {"score": min(100, score), "passed": score >= 70, "warnings": warnings, "tag_count": len(tags)}
