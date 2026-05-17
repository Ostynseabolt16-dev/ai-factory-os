"""Image generation cache and spend protection for AI Factory OS."""

from __future__ import annotations

import json
import os
from datetime import datetime
from hashlib import sha256
from pathlib import Path

from ai_factory.config import PROJECT_ROOT
from ai_factory.generation.openai_image import generate_simple_image_to_file

IMAGE_CACHE_PATH = PROJECT_ROOT / "image_generation_cache.json"
IMAGE_USAGE_LOG = PROJECT_ROOT / "generation_api_usage.log"
IMAGE_SPEND_LIMIT = float(os.getenv("IMAGE_SPEND_LIMIT", "10.00"))
IMAGE_COST_PER_CALL = float(os.getenv("IMAGE_COST_PER_CALL", "0.02"))


def _now() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def _load_cache() -> dict[str, object]:
    if not IMAGE_CACHE_PATH.exists():
        return {"total_spend": 0.0, "items": {}}
    try:
        with IMAGE_CACHE_PATH.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return {"total_spend": float(data.get("total_spend", 0.0)), "items": data.get("items", {})}
    except (json.JSONDecodeError, OSError):
        return {"total_spend": 0.0, "items": {}}


def _save_cache(cache: dict[str, object]) -> None:
    IMAGE_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with IMAGE_CACHE_PATH.open("w", encoding="utf-8") as handle:
        json.dump(cache, handle, indent=2)


def _hash_prompt(prompt: str) -> str:
    return sha256(prompt.strip().encode("utf-8")).hexdigest()


def _write_usage_log(entry: str) -> None:
    IMAGE_USAGE_LOG.parent.mkdir(parents=True, exist_ok=True)
    with IMAGE_USAGE_LOG.open("a", encoding="utf-8") as handle:
        handle.write(entry + "\n")


def get_cached_image_path(prompt: str) -> Path | None:
    cache = _load_cache()
    prompt_hash = _hash_prompt(prompt)
    item = cache.get("items", {}).get(prompt_hash)
    if not item:
        return None
    path_value = item.get("path", "")
    if not path_value:
        return None
    path = Path(path_value)
    if path.exists():
        return path
    return None


def reserve_generation_cost() -> None:
    cache = _load_cache()
    estimated_spend = float(cache.get("total_spend", 0.0)) + IMAGE_COST_PER_CALL
    if estimated_spend > IMAGE_SPEND_LIMIT:
        raise RuntimeError(
            "Image generation would exceed configured spend limit. "
            f"Current spend: ${cache.get('total_spend', 0.0):.2f}, limit: ${IMAGE_SPEND_LIMIT:.2f}."
        )


def cache_image_path(prompt: str, path: Path, model: str = "gpt-image-1") -> None:
    cache = _load_cache()
    prompt_hash = _hash_prompt(prompt)
    cache.setdefault("items", {})[prompt_hash] = {
        "prompt": prompt,
        "path": str(path),
        "model": model,
        "generated_at": _now(),
        "estimated_cost": IMAGE_COST_PER_CALL,
    }
    cache["total_spend"] = float(cache.get("total_spend", 0.0)) + IMAGE_COST_PER_CALL
    _save_cache(cache)
    _write_usage_log(
        f"{_now()} prompt_hash={prompt_hash} model={model} cost={IMAGE_COST_PER_CALL:.4f} path={path}"
    )


def generate_cached_image(prompt: str, output_path: Path, *, model: str = "gpt-image-1") -> Path:
    existing = get_cached_image_path(prompt)
    if existing is not None:
        return existing

    reserve_generation_cost()
    result = generate_simple_image_to_file(prompt, output_path, model=model)
    cache_image_path(prompt, result, model=model)
    return result
