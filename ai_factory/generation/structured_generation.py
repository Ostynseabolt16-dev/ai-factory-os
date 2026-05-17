"""Structured product concept generation and validation for AI Factory OS."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from openai import OpenAI

import ai_factory.config  # noqa: F401
from ai_factory.generation.image_cache import generate_cached_image
from ai_factory.generation.openai_image import get_openai_client

DEFAULT_PRODUCT_MODEL = os.getenv("OPENAI_PRODUCT_MODEL", "gpt-4o-mini")
MAX_TAG_LEN = 20
MIN_TAG_COUNT = 5
MAX_TAG_COUNT = 13
MIN_TITLE_LEN = 15
MAX_TITLE_LEN = 140
MIN_DESCRIPTION_LEN = 80
MAX_DESCRIPTION_LEN = 1200
IMAGE_OUTPUT_DIR = ai_factory.config.PROJECT_ROOT / "designs"

REQUIRED_PRODUCT_FIELDS = [
    "idea",
    "niche",
    "title",
    "description",
    "tags",
    "image_prompt",
    "trend_score",
    "confidence_score",
]


def _strip_json_fence(content: str) -> str:
    content = content.strip()
    fenced = re.match(r"```(?:json)?\n(.*)\n```$", content, flags=re.S)
    if fenced:
        return fenced.group(1).strip()
    return content


def _normalize_tags(tags: Any) -> list[str]:
    if not isinstance(tags, list):
        return []
    normalized: list[str] = []
    for tag in tags:
        if not isinstance(tag, str):
            continue
        tag_text = re.sub(r"\s+", " ", tag.strip().lower())
        if not tag_text:
            continue
        if len(tag_text) > MAX_TAG_LEN:
            tag_text = tag_text[:MAX_TAG_LEN].strip()
        if tag_text not in normalized:
            normalized.append(tag_text)
        if len(normalized) >= MAX_TAG_COUNT:
            break
    return normalized


def _parse_json_object(content: str) -> dict[str, Any]:
    output = _strip_json_fence(content)
    data = json.loads(output)
    if not isinstance(data, dict):
        raise ValueError("Model returned JSON that is not an object.")
    return data


def _is_markdown_header(value: str) -> bool:
    return bool(re.search(r"(?m)^#{1,6} ", value))


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _int_value(value: Any, default: int = 0) -> int:
    try:
        return int(float(str(value or "").strip()))
    except ValueError:
        return default


def _log_generation_error(context: str, error: str, payload: str | None = None) -> None:
    log_path = ai_factory.config.PROJECT_ROOT / "generation_errors.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"{context} | {error}\n")
        if payload is not None:
            handle.write(f"payload: {payload}\n")


def validate_generated_product(product: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(product, dict):
        raise ValueError("Generated product must be a JSON object.")

    for field in REQUIRED_PRODUCT_FIELDS:
        if field not in product:
            errors.append(f"Missing field: {field}")

    idea = _clean_text(product.get("idea"))
    niche = _clean_text(product.get("niche"))
    title = _clean_text(product.get("title"))
    description = _clean_text(product.get("description"))
    image_prompt = _clean_text(product.get("image_prompt"))
    tags = _normalize_tags(product.get("tags"))
    trend_score = _int_value(product.get("trend_score"))
    confidence_score = _int_value(product.get("confidence_score"))

    if not idea:
        errors.append("Idea is required.")
    if not niche:
        errors.append("Niche is required.")
    if _is_markdown_header(title) or not title:
        errors.append("Title must be plain text and not a markdown heading.")
    if not (MIN_TITLE_LEN <= len(title) <= MAX_TITLE_LEN):
        errors.append(f"Title length must be between {MIN_TITLE_LEN} and {MAX_TITLE_LEN} characters.")
    if "```" in description or _is_markdown_header(description):
        errors.append("Description must not include markdown fences or heading syntax.")
    if not (MIN_DESCRIPTION_LEN <= len(description) <= MAX_DESCRIPTION_LEN):
        errors.append(f"Description length must be between {MIN_DESCRIPTION_LEN} and {MAX_DESCRIPTION_LEN} characters.")
    if not tags:
        errors.append("Tags must be a non-empty array of strings.")
    if not (MIN_TAG_COUNT <= len(tags) <= MAX_TAG_COUNT):
        errors.append(f"Tags count must be between {MIN_TAG_COUNT} and {MAX_TAG_COUNT}.")
    if not image_prompt:
        errors.append("Image prompt is required.")
    if _is_markdown_header(image_prompt):
        errors.append("Image prompt must be plain text, not markdown.")
    if not (0 <= trend_score <= 100):
        errors.append("Trend score must be an integer between 0 and 100.")
    if not (0 <= confidence_score <= 100):
        errors.append("Confidence score must be an integer between 0 and 100.")

    if errors:
        raise ValueError("; ".join(errors))

    return {
        "idea": idea,
        "niche": niche,
        "title": title,
        "description": description,
        "tags": tags,
        "image_prompt": image_prompt,
        "trend_score": trend_score,
        "confidence_score": confidence_score,
    }


def score_product_concept(product: dict[str, Any]) -> int:
    score = 0
    score += min(40, int(product.get("trend_score", 0)) * 0.4)
    score += min(40, int(product.get("confidence_score", 0)) * 0.4)
    score += min(10, len(product.get("tags", [])))
    score += min(5, max(0, len(str(product.get("title", ""))) - MIN_TITLE_LEN) // 10)
    score += min(5, max(0, len(str(product.get("description", ""))) - MIN_DESCRIPTION_LEN) // 100)
    if product.get("image_prompt") and len(str(product.get("image_prompt"))) < 180:
        score += 5
    return min(100, max(0, int(score)))


def rank_generated_products(products: list[dict[str, Any]], top_n: int = 10) -> list[dict[str, Any]]:
    for product in products:
        product["validation_score"] = score_product_concept(product)
    ranked = sorted(products, key=lambda row: row["validation_score"], reverse=True)
    return ranked[:top_n]


def _product_prompt(idea: str) -> str:
    return (
        f"Raw product idea: {idea}\n\n"
        "Create one validated product concept for Etsy print-on-demand. "
        "Return valid JSON only, no markdown, no extra explanation. "
        "The JSON object must contain exactly these keys: idea, niche, title, description, tags, image_prompt, trend_score, confidence_score. "
        "Use tags as buyer search phrases. Trend score and confidence score must be integers between 0 and 100. "
        "The image_prompt should be a descriptive art prompt for a clean, cute product design suitable for Shopify or Etsy print-on-demand."
    )


def generate_structured_product_from_idea(idea: str, model: str | None = None) -> dict[str, Any]:
    idea_text = str(idea or "").strip()
    if not idea_text:
        raise ValueError("Idea must be a non-empty string.")

    client: OpenAI = get_openai_client()
    response = client.chat.completions.create(
        model=model or DEFAULT_PRODUCT_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "You are a product concept generator for quick-turn Etsy listings."},
            {"role": "user", "content": _product_prompt(idea_text)},
        ],
        temperature=0.6,
    )

    raw_content = response.choices[0].message.content
    product = _parse_json_object(raw_content)
    try:
        validated_product = validate_generated_product(product)
    except ValueError as exc:
        _log_generation_error("Product validation failed", str(exc), raw_content)
        raise
    return validated_product


def generate_structured_products_from_ideas(ideas: list[str]) -> list[dict[str, Any]]:
    valid_products: list[dict[str, Any]] = []
    for idea in ideas:
        try:
            product = generate_structured_product_from_idea(idea)
            valid_products.append(product)
        except Exception as exc:
            _log_generation_error(f"Skipping idea: {idea}", str(exc), idea)
    return valid_products


def generate_and_cache_concept_image(product: dict[str, Any], stem: str) -> Path:
    prompt = product["image_prompt"]
    output_path = IMAGE_OUTPUT_DIR / f"{stem}.png"
    return generate_cached_image(prompt, output_path)


def run_structured_batch_from_ideas(ideas: list[str], daily_limit: int = 10) -> list[dict[str, Any]]:
    products = generate_structured_products_from_ideas(ideas)
    if not products:
        return []
    return rank_generated_products(products, top_n=daily_limit)
