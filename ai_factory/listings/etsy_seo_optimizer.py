"""Local Etsy SEO scoring and improvement helpers."""

from __future__ import annotations


def _words(value: str) -> list[str]:
    return [word.strip(".,|-/& ").lower() for word in (value or "").replace("|", " ").split() if word.strip(".,|-/& ")]


def analyze_title(title: str) -> dict[str, object]:
    """Score title readability and keyword coverage."""
    words = _words(title)
    repeated = sorted({word for word in words if words.count(word) > 2 and len(word) > 3})
    warnings: list[str] = []
    score = 0
    if 55 <= len(title) <= 140:
        score += 40
    else:
        warnings.append("title should be 55-140 characters for readable Etsy SEO")
        score += 15 if title else 0
    if len(set(words)) >= max(4, int(len(words) * 0.7)):
        score += 25
    else:
        warnings.append("title repeats too many keywords")
    if any(term in title.lower() for term in ["sticker", "stickers", "decal", "planner"]):
        score += 20
    else:
        warnings.append("title should include clear product terms")
    if not repeated:
        score += 15
    return {"score": min(100, score), "warnings": warnings, "repeated_keywords": repeated, "length": len(title)}


def analyze_tags(tags: str | list[str]) -> dict[str, object]:
    """Score Etsy tag diversity and duplicate keyword risk."""
    tag_list = tags if isinstance(tags, list) else [tag.strip() for tag in (tags or "").replace(",", "|").split("|")]
    tag_list = [tag.lower() for tag in tag_list if tag.strip()]
    warnings: list[str] = []
    score = 0
    if len(tag_list) >= 13:
        score += 35
    else:
        warnings.append("use all 13 Etsy tags")
        score += min(25, len(tag_list) * 2)
    if len(set(tag_list)) == len(tag_list):
        score += 25
    else:
        warnings.append("duplicate tags detected")
    if all(len(tag) <= 20 for tag in tag_list):
        score += 20
    else:
        warnings.append("some tags are over Etsy's 20 character limit")
    words = [word for tag in tag_list for word in _words(tag)]
    duplicate_words = sorted({word for word in words if words.count(word) > 4 and len(word) > 3})
    if not duplicate_words:
        score += 20
    else:
        warnings.append("too many tags repeat the same keyword")
    return {"score": min(100, score), "warnings": warnings, "tag_count": len(tag_list), "duplicate_keywords": duplicate_words}


def score_seo_strength(product: dict[str, str]) -> dict[str, object]:
    """Combine title, tag, and thumbnail readability hints."""
    title = analyze_title(product.get("title", ""))
    tags = analyze_tags(product.get("tags", ""))
    thumbnail_warnings = []
    if not product.get("mockup_paths"):
        thumbnail_warnings.append("missing mockups; thumbnail cannot be evaluated")
    score = round(title["score"] * 0.45 + tags["score"] * 0.45 + (10 if not thumbnail_warnings else 0), 3)
    return {
        "seo_score": score,
        "passed": score >= 70,
        "title": title,
        "tags": tags,
        "mobile_thumbnail_hints": thumbnail_warnings or ["use close-up primary image with large readable stickers"],
    }


def suggest_keyword_expansion(product: dict[str, str]) -> list[str]:
    """Suggest local keyword expansions for Etsy listing experiments."""
    niche = (product.get("niche") or product.get("idea") or "").lower()
    suggestions = ["planner stickers", "laptop decals", "water bottle stickers", "journal stickers"]
    if "anxiety" in niche:
        suggestions.extend(["mental health stickers", "anxiety stickers", "overthinking sticker", "social battery"])
    if "kawaii" not in niche:
        suggestions.append("kawaii stickers")
    return list(dict.fromkeys(suggestions))
