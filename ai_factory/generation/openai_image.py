"""OpenAI Images API helpers — shared by CLI entrypoints."""

from __future__ import annotations

import base64
import os
import re
from pathlib import Path

from openai import OpenAI

# Ensure .env is loaded before reading OPENAI_API_KEY
import ai_factory.config  # noqa: F401

# Style block used by the interactive kawaii generator (keep in sync with product line).
BASE_STYLE_KAWAII = """
cute kawaii vector t-shirt design,
professional Etsy best seller style,
bold clean outlines,
high detail,
centered composition,
vibrant pastel colors,
transparent background,
isolated PNG sticker style,
commercial t-shirt graphic,
cute expressive faces,
high contrast,
polished shading,
balanced composition,
vector illustration quality,
no mockup,
no shirt,
no background,
no watermark,
4k quality
""".strip()


def _client() -> OpenAI:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not set. Add it to your .env file.")
    return OpenAI(api_key=key)


def get_openai_client() -> OpenAI:
    """Shared OpenAI client for image + chat calls (same API key)."""
    return _client()


def _safe_filename_stub(text: str, max_len: int = 20) -> str:
    stub = text[:max_len].strip().replace(" ", "_")
    stub = re.sub(r"[^a-zA-Z0-9._-]", "", stub)
    return stub or "design"


def generate_kawaii_design_to_designs(idea: str, *, stem: str | None = None) -> Path:
    """
    Generate a transparent PNG from a user idea; save under designs/.

    Matches legacy `image_creator.py` behavior (model, size, background).

    If `stem` is set, the file is saved as ``designs/{stem}.png`` (use for unique pipeline filenames).
    Otherwise the filename is derived from the idea text (legacy behavior).
    """
    from ai_factory.config import DESIGNS_DIR

    client = _client()
    final_prompt = f"{idea}, {BASE_STYLE_KAWAII}"

    response = client.images.generate(
        model="gpt-image-1",
        prompt=final_prompt,
        size="1024x1024",
        background="transparent",
    )

    image_b64 = response.data[0].b64_json
    if not image_b64:
        raise RuntimeError("No image data returned from OpenAI.")

    image_bytes = base64.b64decode(image_b64)

    DESIGNS_DIR.mkdir(parents=True, exist_ok=True)
    if stem:
        base = re.sub(r"[^a-zA-Z0-9._-]", "", stem.strip()) or "design"
        filename = DESIGNS_DIR / f"{base}.png"
    else:
        filename = DESIGNS_DIR / f"{_safe_filename_stub(idea)}.png"

    with open(filename, "wb") as f:
        f.write(image_bytes)

    return filename


def generate_simple_image_to_file(
    prompt: str,
    output_path: str | Path,
    *,
    model: str = "gpt-image-1",
    size: str = "1024x1024",
    background: str | None = None,
) -> Path:
    """
    Minimal image generation — used by `pipeline.py` (single file output).

    If `background` is None, the API default is used (legacy pipeline had no transparency).
    """
    client = _client()
    kwargs: dict = {"model": model, "prompt": prompt, "size": size}
    if background is not None:
        kwargs["background"] = background

    response = client.images.generate(**kwargs)

    image_b64 = response.data[0].b64_json
    if not image_b64:
        raise RuntimeError("No image data returned from OpenAI.")

    image_bytes = base64.b64decode(image_b64)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "wb") as f:
        f.write(image_bytes)

    return path.resolve()
