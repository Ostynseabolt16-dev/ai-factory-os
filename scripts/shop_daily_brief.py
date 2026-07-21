#!/usr/bin/env python3
"""Print CozyOrbitPrints daily ops brief from local shop state (no Etsy API).

Reads:
  - designs/listings/SHOP_STATE.md
  - sales_log.csv

Usage:
  cd ~/ai && .venv/bin/python scripts/shop_daily_brief.py
"""

from __future__ import annotations

import argparse
import csv
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHOP_STATE = ROOT / "designs/listings/SHOP_STATE.md"
SALES_LOG = ROOT / "sales_log.csv"
LISTINGS_DIR = ROOT / "designs/listings"
DESIGNS_DIR = ROOT / "designs"

BLOCKED_EXPORTS = {
    "c6_variant_B_collection_UPLOAD_TO_PRINTIFY.png": "Regen with no-plate prompt when OpenAI credits return (Pillow fix abandoned)",
}

EXPORT_TO_LISTING = {
    "c5_variant_B_blackwheels_plate_UPLOAD_TO_PRINTIFY.png": "C5_VARIANT_B.md",  # may not exist as separate file
    "c6_variant_B_collection_UPLOAD_TO_PRINTIFY.png": "C6_VARIANT_B.md",
    "c7_variant_B_collection_UPLOAD_TO_PRINTIFY.png": "C7_VARIANT_B.md",
    "c7_torch_red_collection_UPLOAD_TO_PRINTIFY.png": "C7_TORCH_RED.md",
    "c5_torch_red_collection_UPLOAD_TO_PRINTIFY.png": "C5_TORCH_RED.md",
    "c7_laguna_blue_collection_UPLOAD_TO_PRINTIFY.png": "C7_LAGUNA_BLUE.md",
    "c7_velocity_yellow_collection_UPLOAD_TO_PRINTIFY.png": "C7_VELOCITY_YELLOW.md",
    "c6_atomic_orange_collection_UPLOAD_TO_PRINTIFY.png": "C6_ATOMIC_ORANGE.md",
    "c5_black_collection_UPLOAD_TO_PRINTIFY.png": "C5_BLACK.md",
    "c4_popup_gothic_collection_UPLOAD_TO_PRINTIFY.png": "C4_POPUP_GOTHIC.md",
}


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _parse_last_updated(text: str) -> str | None:
    match = re.search(r"\*\*Last updated:\*\*\s*(.+)", text)
    return match.group(1).strip() if match else None


def _parse_ads_snapshot(text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    in_ads = False
    for line in text.splitlines():
        if line.startswith("## Etsy Ads snapshot"):
            in_ads = True
            continue
        if in_ads and line.startswith("## "):
            break
        if not in_ads or not line.startswith("|") or "---" in line or "Listing" in line:
            continue
        parts = [p.strip() for p in line.strip("|").split("|")]
        if len(parts) >= 4:
            rows.append({"listing": parts[0], "views": parts[1], "roas": parts[2], "orders": parts[3]})
    return rows


def _parse_filename(cell: str) -> str | None:
    cell = cell.strip().strip("`")
    match = re.search(r"([\w./-]+\.png)", cell)
    return Path(match.group(1)).name if match else None


def _parse_test_exports(text: str) -> list[tuple[str, str]]:
    """Return (label, printify filename) from Test / new table."""
    pairs: list[tuple[str, str]] = []
    in_section = False
    for line in text.splitlines():
        if line.startswith("### Test / new"):
            in_section = True
            continue
        if in_section and line.startswith("### "):
            break
        if not in_section or not line.startswith("|"):
            continue
        if "---" in line or "Listing" in line:
            continue
        parts = [p.strip() for p in line.strip("|").split("|")]
        if len(parts) < 3:
            continue
        export_name = _parse_filename(parts[2])
        if export_name:
            pairs.append((parts[0], export_name))
    return pairs


def _parse_unchecked_checklist(text: str) -> list[str]:
    items: list[str] = []
    for line in text.splitlines():
        if line.strip().startswith("- [ ]"):
            items.append(line.strip()[5:].strip())
    return items


def _load_sales() -> list[dict[str, str]]:
    if not SALES_LOG.exists():
        return []
    with SALES_LOG.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _net_sales(rows: list[dict[str, str]]) -> tuple[int, int]:
    units = 0
    orders = 0
    for row in rows:
        notes = (row.get("notes") or "").lower()
        if "cancel" in notes or "refund" in notes:
            continue
        try:
            qty = int(float(row.get("qty") or 0))
        except ValueError:
            qty = 0
        if qty <= 0:
            continue
        orders += 1
        units += qty
    return orders, units


def _recent_sale(rows: list[dict[str, str]]) -> dict[str, str] | None:
    valid = [
        r
        for r in rows
        if "cancel" not in (r.get("notes") or "").lower()
        and "refund" not in (r.get("notes") or "").lower()
    ]
    if not valid:
        return None
    return max(enumerate(valid), key=lambda item: (item[1].get("order_date") or "", item[0]))[1]


def _ad_actions(ads: list[dict[str, str]]) -> list[str]:
    actions: list[str] = []
    for row in ads:
        listing = row["listing"]
        roas = row["roas"]
        try:
            roas_val = float(roas)
        except ValueError:
            roas_val = 0.0
        if listing.lower().startswith("c6") and roas_val == 0:
            actions.append(f"Watch **{listing}** ads (ROAS {roas}, 2 organic sales — keep running for more data)")
        elif roas_val >= 5:
            actions.append(f"Keep funding **{listing}** (ROAS {roas})")
        elif listing.lower().startswith("c4") and roas_val >= 15:
            actions.append(f"Protect **{listing}** — best ROAS ({roas})")
        elif listing.lower().startswith("c8") and roas_val == 0:
            actions.append(f"Do not fund **{listing}** ads until hero/thumbnail fixed")
    return actions


def _ready_to_list(test_exports: list[tuple[str, str]]) -> tuple[list[str], list[str], list[str]]:
    ready: list[str] = []
    missing_copy: list[str] = []
    blocked: list[str] = []
    for label, export_name in test_exports:
        export_path = DESIGNS_DIR / export_name
        if not export_path.exists():
            continue
        if export_name in BLOCKED_EXPORTS:
            blocked.append(f"{label} → `{export_name}` — {BLOCKED_EXPORTS[export_name]}")
            continue
        listing_file = EXPORT_TO_LISTING.get(export_name)
        want = listing_file or f"{export_name.replace('_UPLOAD_TO_PRINTIFY.png', '').upper()}.md"
        if (LISTINGS_DIR / want).exists():
            ready.append(f"{label} → `{export_name}` + `{want}` (manual Etsy paste)")
        else:
            missing_copy.append(f"{label} → `{export_name}` — write `designs/listings/{want}` first")
    return ready, missing_copy, blocked


def build_brief() -> str:
    state = _read_text(SHOP_STATE)
    sales = _load_sales()
    orders, units = _net_sales(sales)
    recent = _recent_sale(sales)
    ads = _parse_ads_snapshot(state)
    test_exports = _parse_test_exports(state)
    checklist = _parse_unchecked_checklist(state)
    ready, missing_copy, blocked = _ready_to_list(test_exports)
    ad_actions = _ad_actions(ads)

    lines: list[str] = []
    lines.append("# CozyOrbitPrints — Daily Brief")
    lines.append("")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"Shop state file: `{SHOP_STATE.relative_to(ROOT)}`")
    updated = _parse_last_updated(state)
    if updated:
        lines.append(f"SHOP_STATE last updated: {updated}")
    lines.append("")
    lines.append("> Local files only — no Etsy API. Refresh ads/sales in SHOP_STATE + sales_log.csv when numbers change.")
    lines.append("")

    lines.append("## Snapshot")
    lines.append(f"- Net orders: **{orders}** ({units} units)")
    if recent:
        lines.append(
            f"- Latest logged sale: **{recent.get('order_date')}** — {recent.get('listing', '')[:60]}…"
            if len(recent.get("listing") or "") > 60
            else f"- Latest logged sale: **{recent.get('order_date')}** — {recent.get('listing')}"
        )
    lines.append(f"- Etsy shop: https://www.etsy.com/shop/CozyOrbitPrints")
    lines.append("")

    lines.append("## Do these 3 things (manual, ~15 min)")
    tonight: list[str] = []
    trim_actions = [a for a in ad_actions if "Trim" in a or "pause" in a.lower() or "Do not fund" in a]
    fund_actions = [a for a in ad_actions if a not in trim_actions]
    if trim_actions:
        tonight.append(trim_actions[0])
    elif fund_actions:
        tonight.append(fund_actions[0])
    if missing_copy:
        tonight.append(f"Pick one ready export and write listing copy: {missing_copy[0].split('—')[0].strip()}")
    elif ready:
        tonight.append(f"List next (copy ready): {ready[0].split('→')[0].strip()}")
    if checklist:
        tonight.append(f"Shop admin: {checklist[0]}")
    if len(tonight) < 3:
        tonight.append("Paste fresh Etsy Ads stats into SHOP_STATE → Etsy Ads snapshot (if >7 days old)")
    if len(tonight) < 3:
        tonight.append("Log any new orders to sales_log.csv")
    for i, item in enumerate(tonight[:3], start=1):
        lines.append(f"{i}. {item}")
    lines.append("")

    if ad_actions:
        lines.append("## Ads (from SHOP_STATE snapshot)")
        for row in ads:
            lines.append(f"- {row['listing']}: {row['views']} views, ROAS {row['roas']}, ad orders {row['orders']}")
        lines.append("")

    if ready:
        lines.append("## Ready to list (export + listing .md exist)")
        lines.extend(f"- {item}" for item in ready)
        lines.append("")

    if missing_copy:
        lines.append("## Has Printify export — needs listing .md")
        lines.extend(f"- {item}" for item in missing_copy)
        lines.append("")

    if blocked:
        lines.append("## Blocked")
        lines.extend(f"- {item}" for item in blocked)
        lines.append("")

    if checklist:
        lines.append("## Shop checklist (unchecked)")
        lines.extend(f"- {item}" for item in checklist)
        lines.append("")

    lines.append("## Agent reminders")
    lines.append("- Do **not** run `scripts/generate_*.py` without explicit user OK (OpenAI credits)")
    lines.append("- Do **not** run `fix_c6_plate_pocket.py` — C6 B = regen when credits return")
    lines.append("- Manual Etsy/Printify workflow only (no API key)")
    lines.append("- Update this brief's source files after you act")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Write brief to file (default: stdout)",
    )
    parser.add_argument(
        "--no-tycoon",
        action="store_true",
        help="Skip rebuilding visualizations/cozy_orbit_tycoon.html",
    )
    args = parser.parse_args()
    brief = build_brief()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(brief, encoding="utf-8")
        print(f"OK  {args.output}")
    else:
        print(brief)

    if not args.no_tycoon:
        try:
            import build_tycoon_hq as tycoon

            data = tycoon.write_outputs(tycoon.OUT_DEFAULT)
            print(
                f"OK  Tycoon HQ refreshed ({data['snapshot']['orders']} orders) → "
                f"{tycoon.OUT_DEFAULT.relative_to(ROOT)}"
            )
        except Exception as exc:  # noqa: BLE001 — brief should still print
            print(f"WARN  Tycoon HQ rebuild skipped: {exc}")


if __name__ == "__main__":
    main()
