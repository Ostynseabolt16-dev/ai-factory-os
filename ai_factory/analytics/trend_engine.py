"""Lightweight local-first trend scoring and opportunity analysis engine.

Scores products without external APIs using:
- Title quality metrics
- Tag quality and diversity
- Listing metadata completeness
- Keyword density analysis
- Niche market saturation signals

All scoring is marketplace-agnostic and local-only.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

from ai_factory.products.product_manager import read_products, write_products


def calculate_title_quality(title: str) -> int:
    """Score title quality 0-100.
    
    Factors:
    - Length (optimal 50-80 chars)
    - Keyword count (2-5 keywords)
    - Special chars and separators
    - Avoid all-caps or clickbait
    """
    if not title or not isinstance(title, str):
        return 0
    
    title = title.strip()
    length = len(title)
    score = 0
    
    # Length penalty (optimal range 50-80)
    if 50 <= length <= 80:
        score += 40
    elif 40 <= length <= 100:
        score += 25
    elif length >= 20:
        score += 10
    
    # Word count (3-8 words is good)
    words = title.split()
    word_count = len(words)
    if 3 <= word_count <= 8:
        score += 25
    elif 2 <= word_count <= 10:
        score += 15
    
    # Avoid all caps penalty
    caps_count = sum(1 for c in title if c.isupper())
    if caps_count > length * 0.5:
        score = max(0, score - 15)
    
    # Check for separator usage (dash, slash, pipe)
    if any(sep in title for sep in [" - ", " | ", " / ", ": "]):
        score += 15
    
    # Avoid excessive special chars
    special_count = sum(1 for c in title if c in "!@#$%^&*()_+=<>?")
    if special_count > 3:
        score = max(0, score - 10)
    
    return min(100, max(0, score))


def calculate_tag_quality(tags_str: str) -> int:
    """Score tag quality 0-100.
    
    Factors:
    - Number of tags (should be 5-13 for most platforms)
    - Tag length (2-3 words each)
    - No duplicate tags
    - Avoid generic single-word tags
    - Character usage efficiency
    """
    if not tags_str or not isinstance(tags_str, str):
        return 0
    
    # Split on pipe or comma
    tags = [t.strip() for t in re.split(r'[|,;]', tags_str) if t.strip()]
    
    if not tags:
        return 0
    
    score = 0
    tag_count = len(tags)
    
    # Optimal tag count: 5-13 (varies by platform)
    if 5 <= tag_count <= 13:
        score += 40
    elif 3 <= tag_count <= 15:
        score += 25
    elif 2 <= tag_count <= 20:
        score += 15
    
    # Check for duplicates
    unique_tags = len(set(tags))
    if unique_tags == tag_count:
        score += 20
    elif unique_tags > tag_count * 0.8:
        score += 10
    
    # Tag length analysis
    tag_words = [len(t.split()) for t in tags]
    avg_words = sum(tag_words) / len(tag_words)
    
    # Prefer 1-3 word tags
    if 1 <= avg_words <= 3:
        score += 20
    elif 1 <= avg_words <= 4:
        score += 10
    
    # Avoid very short (single char) or very long tags
    too_short = sum(1 for t in tags if len(t) < 2)
    too_long = sum(1 for t in tags if len(t) > 40)
    
    if too_short > 0 or too_long > 0:
        score = max(0, score - (too_short + too_long) * 5)
    
    return min(100, max(0, score))


def calculate_listing_completeness(
    title: str,
    tags: str,
    description: str,
    category: str = "",
    mockup_count: int = 0,
) -> int:
    """Score listing metadata completeness 0-100.
    
    Factors:
    - Title present and reasonable length
    - Tags present and diverse
    - Description present and length
    - Category specified
    - Mockup/image count (usually minimum 1, optimal 2-4)
    """
    score = 0
    
    # Title: 0-25 points
    if title and len(title.strip()) >= 20:
        score += 25
    elif title and len(title.strip()) >= 10:
        score += 15
    
    # Tags: 0-25 points
    if tags:
        tags_list = [t.strip() for t in re.split(r'[|,;]', tags) if t.strip()]
        if len(tags_list) >= 5:
            score += 25
        elif len(tags_list) >= 3:
            score += 15
        else:
            score += 5
    
    # Description: 0-25 points
    if description:
        desc_len = len(description.strip())
        if desc_len >= 150:
            score += 25
        elif desc_len >= 80:
            score += 15
        elif desc_len >= 30:
            score += 8
    
    # Category: 0-15 points
    if category and len(category.strip()) > 0:
        score += 15
    
    # Mockups/images: 0-10 points
    if mockup_count >= 3:
        score += 10
    elif mockup_count == 2:
        score += 7
    elif mockup_count == 1:
        score += 4
    
    return min(100, max(0, score))


def calculate_keyword_density(title: str, tags: str, description: str = "") -> dict[str, Any]:
    """Analyze keyword frequency and distribution.
    
    Returns:
    {
        "keyword_frequency": Counter of words in title/tags,
        "unique_keywords": count of unique keywords,
        "density_score": 0-100 rating,
        "top_keywords": list of top 5 keywords,
    }
    """
    text = f"{title} {tags} {description}".lower()
    
    # Remove punctuation, split into words
    words = re.findall(r'\b[a-z0-9]{2,}\b', text)
    
    if not words:
        return {
            "keyword_frequency": Counter(),
            "unique_keywords": 0,
            "density_score": 0,
            "top_keywords": [],
        }
    
    keyword_counter = Counter(words)
    unique_keywords = len(keyword_counter)
    total_keywords = len(words)
    
    # Density: avoid very high repetition (>30%) or too sparse
    max_freq = keyword_counter.most_common(1)[0][1] if keyword_counter else 0
    repetition_ratio = max_freq / total_keywords if total_keywords > 0 else 0
    
    density_score = 100
    if repetition_ratio > 0.3:
        density_score -= (repetition_ratio - 0.3) * 100
    
    # Bonus for good keyword spread
    if unique_keywords > total_keywords * 0.5:
        density_score = min(100, density_score + 10)
    
    return {
        "keyword_frequency": keyword_counter,
        "unique_keywords": unique_keywords,
        "density_score": max(0, min(100, int(density_score))),
        "top_keywords": [w for w, _ in keyword_counter.most_common(5)],
    }


def calculate_saturation_score(
    niche: str,
    all_products: list[dict[str, str]],
) -> int:
    """Score niche saturation 0-100 (higher = more saturated).
    
    Factors:
    - Product count in niche
    - Tag overlap with other niche products
    - Title keyword overlap
    
    Returns 0 for new/fresh niche, 100 for highly saturated.
    """
    if not niche:
        return 0
    
    niche_products = [p for p in all_products if (p.get("niche") or "").strip().lower() == niche.lower()]
    niche_count = len(niche_products)
    
    # Base saturation from product count
    if niche_count == 0:
        saturation = 0
    elif niche_count <= 3:
        saturation = 15
    elif niche_count <= 8:
        saturation = 35
    elif niche_count <= 15:
        saturation = 55
    elif niche_count <= 25:
        saturation = 75
    else:
        saturation = 90
    
    # Check tag overlap if we have multiple products
    if niche_count > 1:
        all_tags = []
        for p in niche_products:
            tags = [t.strip().lower() for t in re.split(r'[|,;]', p.get("tags") or "") if t.strip()]
            all_tags.extend(tags)
        
        if all_tags:
            tag_counter = Counter(all_tags)
            most_common_freq = tag_counter.most_common(1)[0][1]
            tag_overlap_ratio = most_common_freq / len(all_tags) if all_tags else 0
            saturation = min(100, int(saturation + (tag_overlap_ratio * 20)))
    
    return min(100, max(0, saturation))


def calculate_opportunity_score(
    product: dict[str, str],
    all_products: list[dict[str, str]],
) -> int:
    """Score product opportunity 0-100 (higher = more opportunity).
    
    Factors:
    - High quality metadata (title, tags, description)
    - Low niche saturation
    - Unique title/tag combination in niche
    - Complete listing metadata
    
    This is the inverse of saturation + quality bonus.
    """
    niche = product.get("niche") or ""
    title = product.get("title") or ""
    tags = product.get("tags") or ""
    description = product.get("description") or ""
    mockup_count = len([p.strip() for p in (product.get("mockup_paths") or "").split("|") if p.strip()])
    
    # Quality components
    title_quality = calculate_title_quality(title)
    tag_quality = calculate_tag_quality(tags)
    completeness = calculate_listing_completeness(
        title=title,
        tags=tags,
        description=description,
        category=product.get("estimated_category") or "",
        mockup_count=mockup_count,
    )
    
    quality_score = (title_quality * 0.3 + tag_quality * 0.3 + completeness * 0.4) / 100
    
    # Saturation impact (lower saturation = higher opportunity)
    saturation = calculate_saturation_score(niche, all_products)
    saturation_factor = (100 - saturation) / 100  # Invert: low saturation = high factor
    
    # Uniqueness in niche (check if title/tags are unique)
    niche_products = [p for p in all_products if (p.get("niche") or "").strip().lower() == niche.lower()]
    uniqueness = 1.0
    
    if niche_products:
        my_tags = set(t.strip().lower() for t in re.split(r'[|,;]', tags) if t.strip())
        duplicate_matches = 0
        
        for other in niche_products:
            if other.get("id") != product.get("id"):
                other_tags = set(t.strip().lower() for t in re.split(r'[|,;]', other.get("tags") or "") if t.strip())
                overlap = len(my_tags & other_tags)
                if overlap > 0:
                    duplicate_matches += 1
        
        uniqueness = 1.0 - (min(duplicate_matches, 5) * 0.1)
    
    # Combine factors
    opportunity = (quality_score * 0.5 + saturation_factor * 0.3 + uniqueness * 0.2) * 100
    
    return min(100, max(0, int(opportunity)))


def score_single_product(
    product: dict[str, str],
    all_products: list[dict[str, str]],
) -> dict[str, int | str]:
    """Calculate all scores for a single product.
    
    Returns:
    {
        "trend_score": 0-100,
        "saturation_score": 0-100,
        "opportunity_score": 0-100,
        "upload_priority": "critical" | "high" | "medium" | "low",
        "lifecycle_stage": "ideation" | "generation" | "review" | "mockups" | "listing" | "published" | "sales" | "archived",
    }
    """
    niche = product.get("niche") or ""
    title = product.get("title") or ""
    tags = product.get("tags") or ""
    description = product.get("description") or ""
    mockup_count = len([p.strip() for p in (product.get("mockup_paths") or "").split("|") if p.strip()])
    
    # Calculate base scores
    title_quality = calculate_title_quality(title)
    tag_quality = calculate_tag_quality(tags)
    completeness = calculate_listing_completeness(
        title=title,
        tags=tags,
        description=description,
        category=product.get("estimated_category") or "",
        mockup_count=mockup_count,
    )
    
    # Trend score: weighted average of quality metrics
    trend_score = int((title_quality * 0.3 + tag_quality * 0.3 + completeness * 0.4))
    
    # Saturation and opportunity
    saturation_score = calculate_saturation_score(niche, all_products)
    opportunity_score = calculate_opportunity_score(product, all_products)
    
    # Upload priority: based on opportunity + completeness
    priority_score = (opportunity_score * 0.6 + completeness * 0.4)
    
    if priority_score >= 80 and completeness >= 75:
        upload_priority = "critical"
    elif priority_score >= 60 and completeness >= 60:
        upload_priority = "high"
    elif priority_score >= 40:
        upload_priority = "medium"
    else:
        upload_priority = "low"
    
    # Lifecycle stage: based on completeness and status
    status = product.get("status") or "draft"
    if status in ["uploaded", "listed", "sold"]:
        lifecycle_stage = "published"
    elif completeness >= 80 and status in ["mockup_ready", "upload_ready"]:
        lifecycle_stage = "listing"
    elif mockup_count > 0 and status in ["reviewed", "mockup_ready"]:
        lifecycle_stage = "mockups"
    elif title and tags and status in ["draft", "reviewed"]:
        lifecycle_stage = "review"
    elif title or tags:
        lifecycle_stage = "generation"
    else:
        lifecycle_stage = "ideation"
    
    return {
        "trend_score": trend_score,
        "saturation_score": saturation_score,
        "opportunity_score": opportunity_score,
        "upload_priority": upload_priority,
        "lifecycle_stage": lifecycle_stage,
    }


def score_all_products_bulk(path=None):
    """Score all products and update products.csv with scores.
    
    Updates fields:
    - trend_score
    - saturation_score
    - opportunity_score
    - upload_priority
    - lifecycle_stage
    
    Returns count of products scored.
    """
    products = read_products(path)
    scored_count = 0
    
    for product in products:
        scores = score_single_product(product, products)
        product["trend_score"] = str(scores["trend_score"])
        product["saturation_score"] = scores["saturation_score"]
        product["opportunity_score"] = str(scores["opportunity_score"])
        product["upload_priority"] = scores["upload_priority"]
        product["lifecycle_stage"] = scores["lifecycle_stage"]
        scored_count += 1
    
    write_products(products, path)
    return scored_count


def get_top_opportunities(
    product_count: int = 10,
    min_opportunity_score: int = 40,
    path=None,
) -> list[dict[str, str]]:
    """Get top opportunity products sorted by opportunity score."""
    products = read_products(path)
    
    # Filter and score
    candidates = []
    for product in products:
        try:
            opp = int(product.get("opportunity_score") or "0")
            if opp >= min_opportunity_score:
                candidates.append(product)
        except (ValueError, TypeError):
            pass
    
    # Sort by opportunity score descending
    candidates.sort(
        key=lambda p: int(p.get("opportunity_score") or "0"),
        reverse=True,
    )
    
    return candidates[:product_count]


def get_low_quality_listings(
    max_completeness: int = 50,
    path=None,
) -> list[dict[str, str]]:
    """Get listings with low metadata completeness."""
    products = read_products(path)
    
    low_quality = []
    for product in products:
        try:
            completeness = int(product.get("listing_completeness_score") or "0")
            if completeness <= max_completeness and product.get("status") in ["draft", "reviewed", "mockup_ready"]:
                low_quality.append(product)
        except (ValueError, TypeError):
            pass
    
    # Sort by completeness ascending
    low_quality.sort(
        key=lambda p: int(p.get("listing_completeness_score") or "0"),
    )
    
    return low_quality
