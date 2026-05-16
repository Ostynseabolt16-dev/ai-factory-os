"""Etsy listing copy via OpenAI Chat (reuses same API key as image generation)."""

from __future__ import annotations

import json
import os
import re
from typing import Any

from openai import OpenAI

import ai_factory.config  # noqa: F401
from ai_factory.generation.openai_image import get_openai_client

# Etsy-style limits (approximate; good enough for first pipeline).
MAX_TITLE_LEN = 140
MAX_TAG_LEN = 20
TAG_COUNT = 13

# Cheap, capable model for text; override with OPENAI_LISTING_MODEL if you want.
DEFAULT_LISTING_MODEL = "gpt-4o-mini"


def _listing_model() -> str:
    return os.getenv("OPENAI_LISTING_MODEL", DEFAULT_LISTING_MODEL)


def _parse_json_object(content: str) -> dict[str, Any]:
    data = json.loads(content)
    if not isinstance(data, dict):
        raise ValueError("Model did not return a JSON object.")
    return data


def _normalize_tags(tags: Any) -> list[str]:
    if not isinstance(tags, list):
        return []
    out: list[str] = []
    for t in tags:
        if not isinstance(t, str):
            continue
        s = t.strip()
        if not s:
            continue
        s = re.sub(r"\s+", " ", s)
        if len(s) > MAX_TAG_LEN:
            s = s[:MAX_TAG_LEN]
        out.append(s.lower())
    # De-dup preserving order
    seen: set[str] = set()
    uniq: list[str] = []
    for t in out:
        if t not in seen:
            seen.add(t)
            uniq.append(t)
        if len(uniq) >= TAG_COUNT:
            break
    while len(uniq) < TAG_COUNT:
        uniq.append("graphic tee")
    return uniq[:TAG_COUNT]


def generate_etsy_listing_from_idea(idea: str) -> dict[str, str | list[str]]:
    """
    Ask the model for title, description, and exactly 13 tags as JSON.

    Returns dict with keys: title, description, tags (list of 13 str).
    """
    idea = idea.strip()
    if not idea:
        raise ValueError("Idea must be non-empty.")

    client: OpenAI = get_openai_client()
    model = _listing_model()

    system = (
        "You write Etsy listings for print-on-demand t-shirts and accessories. "
        "Follow the user's product idea. Output valid JSON only, no markdown."
    )
    user = f"""
Product idea / design concept:
{idea}

Return a JSON object with exactly these keys:
- "title": Etsy listing title, max {MAX_TITLE_LEN} characters, no ALL CAPS spam, include niche keywords.
- "description": 2-4 short paragraphs: hook, who it is for, occasion/gift angle, care/quality note (generic POD is fine).
- "tags": array of exactly {TAG_COUNT} strings. Each tag max {MAX_TAG_LEN} characters, lowercase,
  no hashtags, no commas inside a tag. Tags should be buyer search phrases (niche + audience + style).

JSON only.
""".strip()

    response = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.7,
    )

    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("Empty response from listing model.")

    data = _parse_json_object(content)
    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()
    tags = _normalize_tags(data.get("tags"))

    if len(title) > MAX_TITLE_LEN:
        title = title[: MAX_TITLE_LEN - 1].rstrip() + "…"

    return {"title": title, "description": description, "tags": tags}
