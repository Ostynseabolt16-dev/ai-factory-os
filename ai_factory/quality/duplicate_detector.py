"""Duplicate and near-duplicate inventory detection."""

from __future__ import annotations

import csv
from difflib import SequenceMatcher

from ai_factory.config import PROJECT_ROOT
from ai_factory.products.product_manager import read_products

DUPLICATE_REPORT_CSV = PROJECT_ROOT / "duplicate_report.csv"


def _overlap(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def detect_duplicate_titles() -> list[dict[str, str]]:
    """Detect highly similar titles."""
    rows = read_products()
    duplicates: list[dict[str, str]] = []
    for index, left in enumerate(rows):
        for right in rows[index + 1 :]:
            ratio = SequenceMatcher(None, left.get("title", "").lower(), right.get("title", "").lower()).ratio()
            if left.get("title") and ratio >= 0.86:
                duplicates.append({"product_id": left["id"], "duplicate_id": right["id"], "reason": "similar_title"})
    return duplicates


def detect_similar_products() -> list[dict[str, str]]:
    """Detect similar filenames/niches or variant lineage duplicates."""
    rows = read_products()
    duplicates: list[dict[str, str]] = []
    for index, left in enumerate(rows):
        for right in rows[index + 1 :]:
            filename_ratio = SequenceMatcher(
                None,
                (left.get("filename") or "").lower(),
                (right.get("filename") or "").lower(),
            ).ratio()
            same_parent = left.get("parent_product_id") and left.get("parent_product_id") == right.get("parent_product_id")
            if filename_ratio >= 0.9 or same_parent:
                duplicates.append({"product_id": left["id"], "duplicate_id": right["id"], "reason": "similar_product"})
    return duplicates


def detect_reused_tags() -> list[dict[str, str]]:
    """Detect products with heavy tag overlap."""
    rows = read_products()
    duplicates: list[dict[str, str]] = []
    for index, left in enumerate(rows):
        left_tags = {tag.strip().lower() for tag in (left.get("tags") or "").split("|") if tag.strip()}
        for right in rows[index + 1 :]:
            right_tags = {tag.strip().lower() for tag in (right.get("tags") or "").split("|") if tag.strip()}
            if _overlap(left_tags, right_tags) >= 0.75:
                duplicates.append({"product_id": left["id"], "duplicate_id": right["id"], "reason": "reused_tags"})
    return duplicates


def generate_duplicate_report() -> list[dict[str, str]]:
    """Write duplicate_report.csv and return findings."""
    findings = detect_duplicate_titles() + detect_similar_products() + detect_reused_tags()
    with DUPLICATE_REPORT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["product_id", "duplicate_id", "reason"])
        writer.writeheader()
        writer.writerows(findings)
    return findings
