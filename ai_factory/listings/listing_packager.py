"""Export local listing packages for manual marketplace upload."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from ai_factory.config import PROJECT_ROOT
from ai_factory.products.product_manager import read_products

EXPORTS_DIR = PROJECT_ROOT / "exports"


def _product(product_id: str | int) -> dict[str, str]:
    target = str(product_id)
    for product in read_products():
        if product.get("id") == target:
            return product
    raise ValueError(f"Product id not found: {product_id}")


def export_listing_package(product_id: str | int) -> Path:
    """Create title/description/tags/metadata/mockups files for manual upload."""
    product = _product(product_id)
    folder = EXPORTS_DIR / f"product_{product_id}"
    mockups_folder = folder / "mockups"
    mockups_folder.mkdir(parents=True, exist_ok=True)

    (folder / "title.txt").write_text(product.get("title", ""), encoding="utf-8")
    (folder / "description.txt").write_text(product.get("description", ""), encoding="utf-8")
    (folder / "tags.txt").write_text((product.get("tags") or "").replace("|", "\n"), encoding="utf-8")
    (folder / "metadata.json").write_text(json.dumps(product, indent=2, sort_keys=True), encoding="utf-8")

    for raw_path in [p for p in (product.get("mockup_paths") or "").split("|") if p.strip()]:
        source = Path(raw_path)
        if not source.is_absolute():
            source = PROJECT_ROOT / source
        if source.exists() and source.is_file():
            shutil.copy2(source, mockups_folder / source.name)

    return folder

