"""Export local listing packages for manual marketplace upload."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from ai_factory.config import PROJECT_ROOT
from ai_factory.products.product_manager import read_products

EXPORTS_DIR = PROJECT_ROOT / "exports"
KNOWN_MOCKUP_ORDER = ["front_shirt", "lifestyle", "hoodie", "mug"]


def _product(product_id: str | int) -> dict[str, str]:
    target = str(product_id)
    for product in read_products():
        if product.get("id") == target:
            return product
    raise ValueError(f"Product id not found: {product_id}")


def _parse_mockup_paths(product: dict[str, str]) -> list[Path]:
    raw = (product.get("mockup_paths") or "").strip()
    if not raw:
        return []
    paths: list[Path] = []
    for segment in raw.split("|"):
        segment = segment.strip()
        if not segment:
            continue
        path = Path(segment)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        paths.append(path)
    return paths


def _order_mockup_paths(paths: list[Path]) -> list[Path]:
    if not paths:
        return paths
    ordered: list[Path] = []
    rest: list[Path] = []
    for key in KNOWN_MOCKUP_ORDER:
        for path in paths:
            if key in path.name.lower() and path not in ordered:
                ordered.append(path)
    for path in paths:
        if path not in ordered:
            rest.append(path)
    return ordered + rest


def export_listing_package(product_id: str | int, export_dir: Path | None = None) -> Path:
    """Create title/description/tags/metadata/mockups files for manual upload."""
    product = _product(product_id)
    export_dir = export_dir or EXPORTS_DIR
    folder = export_dir / f"product_{product_id}"
    mockups_folder = folder / "mockups"
    mockups_folder.mkdir(parents=True, exist_ok=True)

    (folder / "title.txt").write_text(product.get("title", ""), encoding="utf-8")
    (folder / "description.txt").write_text(product.get("description", ""), encoding="utf-8")
    (folder / "tags.txt").write_text((product.get("tags") or "").replace("|", "\n"), encoding="utf-8")
    (folder / "metadata.json").write_text(json.dumps(product, indent=2, sort_keys=True), encoding="utf-8")

    mockup_paths = _order_mockup_paths(_parse_mockup_paths(product))
    images_manifest: list[dict[str, str]] = []
    for source in mockup_paths:
        if source.exists() and source.is_file():
            destination = mockups_folder / source.name
            shutil.copy2(source, destination)
            images_manifest.append({
                "filename": source.name,
                "source_path": str(source),
                "export_path": str(destination),
            })

    manifest = {
        "product_id": str(product_id),
        "title": product.get("title", ""),
        "description": product.get("description", ""),
        "tags": [tag for tag in (product.get("tags") or "").split("|") if tag],
        "mockup_files": images_manifest,
    }
    (folder / "manual_upload.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    return folder

