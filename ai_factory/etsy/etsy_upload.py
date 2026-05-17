"""Etsy upload pipeline for AI Factory OS.

This module keeps the upload workflow local-first while supporting metadata
completion, draft vs publish mode, mockup ordering, upload logging, and
failure recovery.
"""

from __future__ import annotations

import csv
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

from ai_factory.config import ETSY_UPLOAD_LOG_CSV, PROJECT_ROOT
from ai_factory.listings.etsy_copy import draft_listing_from_idea
from ai_factory.listings.listing_packager import export_listing_package
from ai_factory.listings.listing_tracker import create_listing_record
from ai_factory.products.product_manager import (
    get_products_by_status,
    mark_product_uploaded,
    read_products,
    update_product_fields,
    _find_product,
)
from ai_factory.tasks.task_models import now_iso
from ai_factory.visuals.factory_map import build_factory_map

ETSY_API_KEY = os.getenv("ETSY_API_KEY")
ETSY_ACCESS_TOKEN = os.getenv("ETSY_ACCESS_TOKEN")
ETSY_SHOP_ID = os.getenv("ETSY_SHOP_ID")
ETSY_API_BASE_URL = os.getenv("ETSY_API_BASE_URL", "https://api.etsy.com/v3/application")

UPLOAD_LOG_COLUMNS = [
    "queue_id",
    "product_id",
    "platform",
    "publish_mode",
    "status",
    "attempts",
    "last_error",
    "last_attempt_at",
    "created_at",
    "updated_at",
    "listing_id",
    "listing_url",
    "notes",
]

QUEUE_STATUS_PENDING = "pending"
QUEUE_STATUS_PROCESSING = "processing"
QUEUE_STATUS_COMPLETED = "completed"
QUEUE_STATUS_RETRY = "retry"
QUEUE_STATUS_FAILED = "failed"

KNOWN_MOCKUP_ORDER = ["front_shirt", "lifestyle", "hoodie", "mug"]


def _ensure_upload_log() -> None:
    if not ETSY_UPLOAD_LOG_CSV.exists():
        ETSY_UPLOAD_LOG_CSV.parent.mkdir(parents=True, exist_ok=True)
        with ETSY_UPLOAD_LOG_CSV.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=UPLOAD_LOG_COLUMNS)
            writer.writeheader()


def _read_upload_log() -> list[dict[str, str]]:
    _ensure_upload_log()
    with ETSY_UPLOAD_LOG_CSV.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_upload_log(rows: list[dict[str, str]]) -> None:
    _ensure_upload_log()
    with ETSY_UPLOAD_LOG_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=UPLOAD_LOG_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in UPLOAD_LOG_COLUMNS})


def _normalize_publish_mode(value: str | None) -> str:
    if not value:
        return "draft"
    normalized = value.strip().lower()
    return "publish" if normalized == "publish" else "draft"


def _parse_tags(value: str | list[str] | None) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if not value:
        return []
    values = [item.strip() for item in str(value).split("|") if item.strip()]
    return values


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
    lower_names = [path.name.lower() for path in paths]
    for key in KNOWN_MOCKUP_ORDER:
        for path in paths:
            if key in path.name.lower() and path not in ordered:
                ordered.append(path)
    for path in paths:
        if path not in ordered:
            rest.append(path)
    return ordered + rest


def _prepare_listing_metadata(product: dict[str, str]) -> dict[str, Any]:
    title = (product.get("title") or "").strip()
    description = (product.get("description") or "").strip()
    tags = _parse_tags(product.get("tags"))

    if title and description and tags:
        return {"title": title, "description": description, "tags": tags}

    idea = (product.get("idea") or "").strip()
    if not idea:
        raise RuntimeError("Cannot generate Etsy metadata: missing title/description/tags and no idea available.")

    generated = draft_listing_from_idea(idea)
    title = title or str(generated.get("title") or "")
    description = description or str(generated.get("description") or "")
    tags = tags or [str(tag) for tag in generated.get("tags") or []]

    if not title or not description or not tags:
        raise RuntimeError("Generated Etsy metadata was incomplete.")

    return {"title": title, "description": description, "tags": tags}


def _has_api_credentials() -> bool:
    return bool(ETSY_ACCESS_TOKEN and ETSY_SHOP_ID)


def _upload_to_etsy(payload: dict[str, Any]) -> dict[str, Any]:
    if not _has_api_credentials():
        raise RuntimeError("Etsy API credentials are not configured. Set ETSY_ACCESS_TOKEN and ETSY_SHOP_ID.")

    url = f"{ETSY_API_BASE_URL}/shops/{ETSY_SHOP_ID}/listings"
    headers = {
        "Authorization": f"Bearer {ETSY_ACCESS_TOKEN}",
        "x-api-key": ETSY_API_KEY or "",
        "Content-Type": "application/json",
    }
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


def _create_queue_row(product_id: str, publish_mode: str) -> dict[str, str]:
    now = now_iso()
    return {
        "queue_id": str(uuid.uuid4()),
        "product_id": str(product_id),
        "platform": "etsy",
        "publish_mode": _normalize_publish_mode(publish_mode),
        "status": QUEUE_STATUS_PENDING,
        "attempts": "0",
        "last_error": "",
        "last_attempt_at": "",
        "created_at": now,
        "updated_at": now,
        "listing_id": "",
        "listing_url": "",
        "notes": "",
    }


def queue_etsy_upload(product_ids: list[int | str] | None = None, publish_mode: str = "draft") -> dict[str, Any]:
    if product_ids is None:
        products = get_products_by_status("upload_ready")
    else:
        products = [
            _find_product(read_products(), product_id)
            for product_id in product_ids
        ]

    queue_rows = _read_upload_log()
    existing = {row["product_id"] for row in queue_rows}
    queued = 0
    for product in products:
        product_id = (product.get("id") or "").strip()
        if not product_id or product_id in existing:
            continue
        queue_rows.append(_create_queue_row(product_id, publish_mode))
        queued += 1
    _write_upload_log(queue_rows)
    return {"queued": queued, "total_queue": len(queue_rows)}


def get_etsy_upload_queue_report() -> dict[str, Any]:
    rows = _read_upload_log()
    status_counts: dict[str, int] = {}
    for row in rows:
        status = row.get("status") or QUEUE_STATUS_PENDING
        status_counts[status] = status_counts.get(status, 0) + 1
    return {
        "total_jobs": len(rows),
        "status_counts": status_counts,
        "recent_jobs": rows[-5:],
    }


def list_etsy_upload_queue(limit: int = 20) -> list[dict[str, str]]:
    rows = _read_upload_log()
    return rows[-limit:]


def retry_failed_etsy_upload() -> dict[str, int]:
    rows = _read_upload_log()
    updated = 0
    for row in rows:
        if row.get("status") == QUEUE_STATUS_FAILED:
            row["status"] = QUEUE_STATUS_PENDING
            row["attempts"] = "0"
            row["last_error"] = ""
            row["notes"] = "retry_reset"
            row["updated_at"] = now_iso()
            updated += 1
    _write_upload_log(rows)
    return {"retried": updated, "total_queue": len(rows)}


def cleanup_completed_etsy_upload_queue() -> dict[str, int]:
    rows = _read_upload_log()
    kept: list[dict[str, str]] = []
    removed = 0
    for row in rows:
        if row.get("status") == QUEUE_STATUS_COMPLETED:
            removed += 1
            continue
        kept.append(row)
    _write_upload_log(kept)
    return {"removed_completed": removed, "remaining": len(kept)}


def export_etsy_upload_queue_packages(
    product_ids: list[int | str] | None = None,
    export_dir: Path | None = None,
) -> dict[str, Any]:
    rows = [row for row in _read_upload_log() if row.get("status") in {QUEUE_STATUS_PENDING, QUEUE_STATUS_RETRY}]
    if product_ids is not None:
        target_ids = {str(pid) for pid in product_ids}
        rows = [row for row in rows if row.get("product_id") in target_ids]

    exported: list[str] = []
    failed: list[dict[str, str]] = []
    for row in rows:
        product_id = row.get("product_id")
        try:
            path = export_listing_package(product_id, export_dir=export_dir)
            exported.append(str(path))
        except Exception as exc:
            failed.append({"product_id": product_id or "", "error": str(exc)})
    return {"exported": len(exported), "failed": len(failed), "paths": exported, "errors": failed}


def process_etsy_upload_queue(
    dry_run: bool = True,
    publish_mode: str = "draft",
    max_attempts: int = 3,
    limit: int | None = None,
) -> dict[str, Any]:
    queue_rows = _read_upload_log()
    pending_rows = [row for row in queue_rows if row.get("status") in {QUEUE_STATUS_PENDING, QUEUE_STATUS_RETRY}]
    published = 0
    validated = 0
    failed = 0
    updated = 0
    processed = 0

    for row in pending_rows:
        if limit is not None and processed >= limit:
            break

        attempts = int(row.get("attempts") or "0")
        if attempts >= max_attempts:
            row["status"] = QUEUE_STATUS_FAILED
            row["last_error"] = "Max attempts exceeded"
            row["updated_at"] = now_iso()
            failed += 1
            continue

        if not dry_run:
            row["status"] = QUEUE_STATUS_PROCESSING
            row["attempts"] = str(attempts + 1)
            row["last_attempt_at"] = now_iso()
            row["updated_at"] = now_iso()
            _write_upload_log(queue_rows)

        try:
            product_id = row["product_id"]
            product = _find_product(read_products(), product_id)
            metadata = _prepare_listing_metadata(product)
            mockup_paths = _order_mockup_paths(_parse_mockup_paths(product))
            if not mockup_paths:
                raise RuntimeError("No mockups found for upload validation.")

            payload = {
                "title": metadata["title"],
                "description": metadata["description"],
                "tags": metadata["tags"],
                "mockup_paths": [str(path) for path in mockup_paths],
                "publish_state": _normalize_publish_mode(publish_mode),
                "product_id": product_id,
            }

            if dry_run:
                row["status"] = QUEUE_STATUS_PENDING
                row["notes"] = "dry_run_validation"
                row["updated_at"] = now_iso()
                validated += 1
            else:
                result = _upload_to_etsy(payload)
                listing_status = "uploaded" if _normalize_publish_mode(publish_mode) == "draft" else "active"
                external_listing_id = str(result.get("listing_id") or result.get("id") or f"etsy-sim-{uuid.uuid4()}")
                listing_url = str(result.get("listing_url") or result.get("url") or "")

                update_product_fields(product_id, {
                    "title": metadata["title"],
                    "description": metadata["description"],
                    "tags": "|".join(metadata["tags"]),
                    "status": "uploaded",
                    "pipeline_stage": "published",
                    "upload_date": now_iso(),
                    "last_updated_at": now_iso(),
                })
                mark_product_uploaded(product_id)
                create_listing_record(
                    product_id=product_id,
                    platform="etsy",
                    marketplace_listing_id=external_listing_id,
                    listing_url=listing_url,
                    listing_status=listing_status,
                    notes=f"Uploaded via Etsy pipeline ({publish_mode})",
                )

                row["status"] = QUEUE_STATUS_COMPLETED
                row["listing_id"] = external_listing_id
                row["listing_url"] = listing_url
                row["notes"] = str(result.get("notes") or "uploaded")
                row["updated_at"] = now_iso()
                published += 1

        except Exception as exc:
            row["status"] = QUEUE_STATUS_RETRY if attempts + 1 < max_attempts else QUEUE_STATUS_FAILED
            row["last_error"] = str(exc)
            row["notes"] = f"{row.get('notes') or ''} | {exc}"
            row["updated_at"] = now_iso()
            failed += 1

        updated += 1
        processed += 1
        _write_upload_log(queue_rows)

    result = {
        "processed": processed,
        "validated": validated,
        "published": published,
        "failed": failed,
        "remaining": len([row for row in queue_rows if row.get("status") in {QUEUE_STATUS_PENDING, QUEUE_STATUS_RETRY}]),
        "queue_summary": get_etsy_upload_queue_report(),
    }

    if processed > 0:
        build_factory_map()

    return result
