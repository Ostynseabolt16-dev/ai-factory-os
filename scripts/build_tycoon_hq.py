#!/usr/bin/env python3
"""Build CozyOrbitPrints Tycoon HQ — local game-style ops monitor.

Reads the same local sources as shop_daily_brief (no Etsy API):
  - sales_log.csv
  - designs/listings/SHOP_STATE.md

Writes a self-contained HTML file you open in a browser:
  visualizations/cozy_orbit_tycoon.html

Usage:
  cd ~/ai && .venv/bin/python scripts/build_tycoon_hq.py
  open visualizations/cozy_orbit_tycoon.html

Live (keeps HTML+JSON fresh while you edit sales_log / SHOP_STATE):
  .venv/bin/python scripts/build_tycoon_hq.py --serve
  # then open http://127.0.0.1:8765/cozy_orbit_tycoon.html
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
import webbrowser
from collections import Counter, defaultdict
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

import shop_daily_brief as brief  # noqa: E402

OUT_DEFAULT = ROOT / "visualizations" / "cozy_orbit_tycoon.html"
SHOP_URL = "https://www.etsy.com/shop/CozyOrbitPrints"
WATCH_PATHS = (brief.SALES_LOG, brief.SHOP_STATE)
SALE_FIELDS = [
    "order_date",
    "order_id",
    "marketplace",
    "listing",
    "qty",
    "item_price",
    "buyer_shipping",
    "sales_tax",
    "order_total",
    "printify_cost",
    "est_etsy_fees",
    "est_net_profit",
    "traffic_source",
    "shirt_color",
    "size",
    "buyer",
    "notes",
]


def _f(val: str | None) -> float | None:
    if val is None or str(val).strip() == "":
        return None
    try:
        return float(str(val).replace(",", "").replace("$", ""))
    except ValueError:
        return None


def _is_valid_sale(row: dict[str, str]) -> bool:
    notes = (row.get("notes") or "").lower()
    if "cancel" in notes or "refund" in notes:
        return False
    qty = _f(row.get("qty"))
    return qty is not None and qty > 0


def _short_listing(name: str) -> str:
    name = (name or "").strip()
    # Drop long pipe suffixes for HUD labels
    if "|" in name:
        name = name.split("|", 1)[0].strip()
    if len(name) > 42:
        return name[:39] + "…"
    return name or "Unknown listing"


def _marketplace_key(raw: str) -> str:
    m = (raw or "").strip().lower()
    if m == "ebay":
        return "ebay"
    if m == "etsy":
        return "etsy"
    return m or "other"


def _tonight_missions(
    ads: list[dict[str, str]],
    ready: list[str],
    missing_copy: list[str],
    checklist: list[str],
) -> list[str]:
    ad_actions = brief._ad_actions(ads)
    tonight: list[str] = []
    trim = [a for a in ad_actions if "Trim" in a or "pause" in a.lower() or "Do not fund" in a]
    fund = [a for a in ad_actions if a not in trim]
    if trim:
        tonight.append(_strip_md(trim[0]))
    elif fund:
        tonight.append(_strip_md(fund[0]))
    if missing_copy:
        tonight.append(f"Write listing copy: {_strip_md(missing_copy[0].split('—')[0].strip())}")
    elif ready:
        tonight.append(f"List next (copy ready): {_strip_md(ready[0].split('→')[0].strip())}")
    if checklist:
        tonight.append(f"Shop admin: {_strip_md(checklist[0])}")
    if len(tonight) < 3:
        tonight.append("Paste fresh Etsy Ads stats into SHOP_STATE if snapshot is stale")
    if len(tonight) < 3:
        tonight.append("Log any new orders to sales_log.csv")
    return tonight[:3]


def _strip_md(text: str) -> str:
    return re.sub(r"\*+", "", text).strip()


def _station_health(status: str) -> str:
    return {"hot": "hot", "ok": "ok", "warn": "warn", "cold": "cold"}.get(status, "ok")


def _parse_ads_snapshot_date(text: str) -> str | None:
    """Parse date from '## Etsy Ads snapshot (2026-06-26, …)'."""
    match = re.search(
        r"## Etsy Ads snapshot\s*\((\d{4}-\d{2}-\d{2})",
        text,
    )
    return match.group(1) if match else None


def _ads_stale_days(snapshot_date: str | None, today: datetime | None = None) -> int | None:
    if not snapshot_date:
        return None
    today = today or datetime.now()
    try:
        snap = datetime.strptime(snapshot_date, "%Y-%m-%d").date()
    except ValueError:
        return None
    return (today.date() - snap).days


def _parse_mission_log(text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    in_section = False
    for line in text.splitlines():
        if line.startswith("## Tycoon mission log"):
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if not in_section or not line.startswith("|"):
            continue
        if "---" in line or line.strip().startswith("| When") or "When" in line and "Mission" in line:
            continue
        parts = [p.strip() for p in line.strip("|").split("|")]
        if len(parts) >= 2 and parts[0] and parts[1] and parts[1].lower() != "mission":
            rows.append({"when": parts[0], "mission": parts[1]})
    return rows


def _clamp_xp(value: float) -> int:
    return max(0, min(100, int(round(value))))


def log_mission_done(mission: str) -> dict[str, str]:
    """Append a completed mission row to SHOP_STATE.md Tycoon mission log."""
    mission = _strip_md(mission).strip()
    if not mission:
        raise ValueError("Empty mission")
    path = brief.SHOP_STATE
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    safe = mission.replace("|", "/")
    row = f"| {stamp} | {safe} |"
    section_title = "## Tycoon mission log"
    table_header = (
        f"{section_title}\n\n"
        "| When | Mission |\n"
        "|------|------|\n"
    )
    if section_title in text:
        # Append row after the table separator line inside the section
        lines = text.splitlines()
        out: list[str] = []
        inserted = False
        in_section = False
        for line in lines:
            if line.startswith(section_title):
                in_section = True
                out.append(line)
                continue
            if in_section and line.startswith("## ") and not line.startswith(section_title):
                if not inserted:
                    out.append(row)
                    inserted = True
                in_section = False
                out.append(line)
                continue
            if in_section and line.startswith("|") and "---" in line and not inserted:
                out.append(line)
                out.append(row)
                inserted = True
                continue
            out.append(line)
        if not inserted:
            out.append(row)
        text = "\n".join(out).rstrip() + "\n"
    else:
        text = text.rstrip() + "\n\n" + table_header + row + "\n"
    path.write_text(text, encoding="utf-8")
    return {"when": stamp, "mission": safe}


def log_sale(payload: dict) -> dict[str, str]:
    """Append one sale row to sales_log.csv. Required: marketplace, listing, qty."""
    marketplace = str(payload.get("marketplace") or "").strip()
    listing = str(payload.get("listing") or "").strip()
    qty_raw = str(payload.get("qty") or "1").strip() or "1"
    if marketplace not in {"Etsy", "eBay"}:
        raise ValueError("marketplace must be Etsy or eBay")
    if not listing:
        raise ValueError("listing required")
    try:
        qty_val = float(qty_raw)
    except ValueError as exc:
        raise ValueError("qty must be a number") from exc
    if qty_val <= 0:
        raise ValueError("qty must be > 0")

    order_date = str(payload.get("order_date") or "").strip()
    if not order_date:
        order_date = datetime.now().strftime("%Y-%m-%d")
    else:
        try:
            datetime.strptime(order_date, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("order_date must be YYYY-MM-DD") from exc

    def _num(key: str) -> str:
        raw = str(payload.get(key) or "").strip()
        if raw == "":
            return ""
        try:
            return f"{float(raw.replace(',', '').replace('$', '')):.2f}"
        except ValueError as exc:
            raise ValueError(f"{key} must be a number") from exc

    row = {field: "" for field in SALE_FIELDS}
    row["order_date"] = order_date
    row["order_id"] = str(payload.get("order_id") or "").strip()
    row["marketplace"] = marketplace
    row["listing"] = listing
    row["qty"] = str(int(qty_val) if qty_val == int(qty_val) else qty_val)
    row["item_price"] = _num("item_price")
    row["buyer_shipping"] = _num("buyer_shipping")
    row["sales_tax"] = _num("sales_tax")
    row["order_total"] = _num("order_total")
    row["printify_cost"] = _num("printify_cost")
    row["est_etsy_fees"] = _num("est_etsy_fees")
    row["est_net_profit"] = _num("est_net_profit")
    row["traffic_source"] = str(payload.get("traffic_source") or "").strip()
    row["shirt_color"] = str(payload.get("shirt_color") or "").strip()
    row["size"] = str(payload.get("size") or "").strip()
    row["buyer"] = str(payload.get("buyer") or "").strip()
    row["notes"] = str(payload.get("notes") or "").strip()

    path = brief.SALES_LOG
    new_file = not path.exists() or path.stat().st_size == 0
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SALE_FIELDS, extrasaction="ignore")
        if new_file:
            writer.writeheader()
        writer.writerow(row)
    return row

def build_snapshot() -> dict:
    state = brief._read_text(brief.SHOP_STATE)
    sales_raw = brief._load_sales()
    sales = [r for r in sales_raw if _is_valid_sale(r)]
    orders, units = brief._net_sales(sales_raw)
    ads = brief._parse_ads_snapshot(state)
    test_exports = brief._parse_test_exports(state)
    checklist = brief._parse_unchecked_checklist(state)
    ready, missing_copy, blocked = brief._ready_to_list(test_exports)

    revenue = 0.0
    printify = 0.0
    known_profit = 0.0
    profit_n = 0
    by_market: dict[str, dict] = defaultdict(lambda: {"orders": 0, "units": 0, "revenue": 0.0})
    by_listing: Counter[str] = Counter()
    recent_feed: list[dict] = []

    for row in sales:
        qty = int(_f(row.get("qty")) or 0)
        market = _marketplace_key(row.get("marketplace") or "")
        item = _f(row.get("item_price"))
        total = _f(row.get("order_total"))
        pf = _f(row.get("printify_cost"))
        net = _f(row.get("est_net_profit"))

        # Prefer item_price; fall back to order_total for revenue rollup
        rev = item if item is not None else total
        if rev is not None:
            revenue += rev
            by_market[market]["revenue"] += rev
        if pf is not None:
            printify += pf
        if net is not None:
            known_profit += net
            profit_n += 1

        by_market[market]["orders"] += 1
        by_market[market]["units"] += qty
        by_listing[_short_listing(row.get("listing") or "")] += qty

        recent_feed.append(
            {
                "date": row.get("order_date") or "—",
                "market": (row.get("marketplace") or "—").strip() or "—",
                "listing": _short_listing(row.get("listing") or ""),
                "qty": qty,
                "revenue": rev,
                "profit": net,
                "color": (row.get("shirt_color") or "").strip(),
                "source": (row.get("traffic_source") or "").strip(),
                "notes": (row.get("notes") or "").strip()[:120],
            }
        )

    recent_feed.sort(key=lambda r: (r["date"],), reverse=True)
    top_listings = [
        {"name": name, "units": count} for name, count in by_listing.most_common(8) if name
    ]

    ads_rows = []
    for row in ads:
        roas_raw = row.get("roas") or "0"
        try:
            roas_val = float(str(roas_raw).replace(",", ""))
        except ValueError:
            roas_val = 0.0
        ads_rows.append(
            {
                "listing": row["listing"],
                "views": row["views"],
                "roas": roas_raw,
                "roas_val": roas_val,
                "orders": row["orders"],
                "health": "ok" if roas_val >= 2 else ("warn" if roas_val >= 1 else "cold"),
            }
        )

    etsy = by_market.get("etsy", {"orders": 0, "units": 0, "revenue": 0.0})
    ebay = by_market.get("ebay", {"orders": 0, "units": 0, "revenue": 0.0})

    # Station status from real signals
    etsy_health = "ok" if etsy["orders"] >= 5 else "warn"
    ebay_health = "hot" if ebay["orders"] >= 2 else ("ok" if ebay["orders"] else "cold")
    if ads_rows:
        avg_roas = sum(a["roas_val"] for a in ads_rows[:4]) / max(1, min(4, len(ads_rows)))
        ads_health = "ok" if avg_roas >= 2 else ("warn" if avg_roas >= 1 else "cold")
    else:
        ads_health = "cold"
    pipe_health = "warn" if blocked or missing_copy else ("ok" if ready else "cold")

    missions = _tonight_missions(ads, ready, missing_copy, checklist)
    updated = brief._parse_last_updated(state)

    first_date = None
    for row in sales:
        d = (row.get("order_date") or "").strip()
        if d and (first_date is None or d < first_date):
            first_date = d
    shop_day = 0
    if first_date:
        try:
            shop_day = (datetime.now().date() - datetime.strptime(first_date, "%Y-%m-%d").date()).days + 1
        except ValueError:
            shop_day = 0
    # Soft tycoon level: every 5 net orders ≈ one level
    level = max(1, (orders // 5) + 1)
    xp_into_level = orders % 5
    xp_to_next = 5
    xp_pct = int(round(100 * xp_into_level / xp_to_next)) if xp_to_next else 0

    ads_date = _parse_ads_snapshot_date(state)
    ads_age = _ads_stale_days(ads_date)
    ads_stale = ads_age is not None and ads_age > 7
    if ads_stale:
        ads_health = "warn"
        ads_note = (
            f"Ads snapshot dated {ads_date} ({ads_age} days old) — paste fresh Etsy Ads stats into SHOP_STATE."
        )
    else:
        ads_note = "From SHOP_STATE Etsy Ads snapshot — refresh manually when stale."
        if ads_date and ads_age is not None:
            ads_note = f"Snapshot {ads_date} ({ads_age}d ago). " + ads_note

    mission_log = _parse_mission_log(state)
    done_set = {m["mission"].lower() for m in mission_log if m.get("mission")}
    missions_rich = [
        {
            "text": m,
            "display": _humanize_mission(m),
            "done": bool(
                done_set
                and (
                    m.lower() in done_set
                    or any(
                        len(d) > 12 and (m.lower() in d or d in m.lower())
                        for d in done_set
                    )
                )
            ),
        }
        for m in missions
    ]

    # Station XP (0–100) — light game juice from real stats
    avg_top_roas = 0.0
    if ads_rows:
        avg_top_roas = sum(a["roas_val"] for a in ads_rows[:4]) / max(1, min(4, len(ads_rows)))
    station_xp = {
        "hq": _clamp_xp(xp_pct),
        "etsy": _clamp_xp(etsy["orders"] * 5),
        "ebay": _clamp_xp(ebay["orders"] * 20),
        "ads": _clamp_xp(0 if ads_stale else avg_top_roas * 22),
        "pipeline": _clamp_xp(len(ready) * 12 - len(blocked) * 20 + (5 if not missing_copy else 0)),
        "missions": _clamp_xp(40 + sum(20 for m in missions_rich if not m["done"])),
    }

    cursor_prompt = _build_cursor_prompt(missions, ready, missing_copy, blocked, orders, units)

    latest = recent_feed[0] if recent_feed else None
    latest_sale_key = ""
    if latest:
        latest_sale_key = f"{latest['date']}|{latest['market']}|{latest['listing']}|{latest['qty']}"

    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "generated_ts": int(time.time()),
        "shop_state_updated": updated or "unknown",
        "shop_url": SHOP_URL,
        "cursor_prompt": cursor_prompt,
        "live_api": True,
        "snapshot": {
            "orders": orders,
            "units": units,
            "revenue": round(revenue, 2),
            "printify": round(printify, 2),
            "known_profit": round(known_profit, 2),
            "known_profit_orders": profit_n,
            "gross_after_printify": round(revenue - printify, 2),
            "shop_day": shop_day,
            "level": level,
            "first_sale": first_date or "—",
            "xp_into_level": xp_into_level,
            "xp_to_next": xp_to_next,
            "xp_pct": xp_pct,
        },
        "markets": {
            "etsy": {
                "orders": etsy["orders"],
                "units": etsy["units"],
                "revenue": round(etsy["revenue"], 2),
                "health": _station_health(etsy_health),
                "xp": station_xp["etsy"],
                "note": "Primary channel historically; Yellow C5 taken down Jul 2026 (IP).",
            },
            "ebay": {
                "orders": ebay["orders"],
                "units": ebay["units"],
                "revenue": round(ebay["revenue"], 2),
                "health": _station_health(ebay_health),
                "xp": station_xp["ebay"],
                "note": "Converting on Yellow C5; watch Ad Fee General vs tee margin.",
            },
        },
        "ads": {
            "rows": ads_rows,
            "health": _station_health(ads_health),
            "xp": station_xp["ads"],
            "snapshot_date": ads_date,
            "age_days": ads_age,
            "stale": ads_stale,
            "note": ads_note,
        },
        "pipeline": {
            "ready": [_strip_md(x) for x in ready],
            "needs_copy": [_strip_md(x) for x in missing_copy],
            "blocked": [_strip_md(x) for x in blocked],
            "checklist": [_strip_md(x) for x in checklist],
            "health": _station_health(pipe_health),
            "xp": station_xp["pipeline"],
        },
        "top_listings": top_listings,
        "recent_sales": recent_feed[:16],
        "latest_sale_key": latest_sale_key,
        "listing_suggestions": [name for name, _ in by_listing.most_common(20) if name],
        "missions": missions,
        "missions_rich": missions_rich,
        "mission_log": mission_log[-8:],
        "station_xp": station_xp,
        "stations": [
            {
                "id": "hq",
                "label": "HOME",
                "name": "Home",
                "hint": "Money & log sales",
                "sub": f"Level {level} · {xp_into_level}/{xp_to_next} to next",
                "health": "ok",
                "xp": station_xp["hq"],
            },
            {
                "id": "etsy",
                "label": "ETSY",
                "name": "Etsy",
                "hint": "Main shop sales",
                "sub": f"{etsy['orders']} orders",
                "health": etsy_health,
                "xp": station_xp["etsy"],
            },
            {
                "id": "ebay",
                "label": "EBAY",
                "name": "eBay",
                "hint": "Growing channel",
                "sub": f"{ebay['orders']} orders",
                "health": ebay_health,
                "xp": station_xp["ebay"],
            },
            {
                "id": "ads",
                "label": "ADS",
                "name": "Ads",
                "hint": "What ads earn back",
                "sub": (
                    f"Needs update ({ads_age}d old)"
                    if ads_stale
                    else f"{len(ads_rows)} listings tracked"
                ),
                "health": ads_health,
                "xp": station_xp["ads"],
            },
            {
                "id": "pipeline",
                "label": "QUEUE",
                "name": "Queue",
                "hint": "Ready / blocked designs",
                "sub": f"{len(ready)} ready · {len(blocked)} blocked",
                "health": pipe_health,
                "xp": station_xp["pipeline"],
            },
            {
                "id": "missions",
                "label": "TO-DO",
                "name": "To-Do",
                "hint": "Tonight’s 3 jobs",
                "sub": f"{sum(1 for m in missions_rich if not m['done'])} open",
                "health": "hot",
                "xp": station_xp["missions"],
            },
        ],
        "coach": _coach_card(missions_rich, ads_stale, ads_age, ready, missing_copy, blocked),
        "glossary": {
            "roas": "ROAS = money from ads ÷ money spent on ads. Above 2 is good.",
            "printify": "Printify = what you pay to print & ship the shirt.",
            "xp": "Level rises every 5 real orders logged. Just a progress meter.",
            "health": "Green OK · Yellow needs a look · Red / cold = problem or empty",
        },
    }


def _coach_card(
    missions_rich: list[dict],
    ads_stale: bool,
    ads_age: int | None,
    ready: list[str],
    missing_copy: list[str],
    blocked: list[str],
) -> dict:
    """One plain-English next action for the top of the screen."""
    open_missions = [m for m in missions_rich if not m.get("done")]
    if ads_stale:
        return {
            "eyebrow": "Needs attention",
            "title": "Ads numbers are out of date",
            "body": (
                f"Your Etsy Ads snapshot is {ads_age} days old. "
                "Open the Ads station, then paste fresh stats into SHOP_STATE when you can."
            ),
            "station": "ads",
            "cta": "Open Ads",
        }
    if open_missions:
        top = _humanize_mission(open_missions[0]["text"])
        return {
            "eyebrow": "Do this next",
            "title": top,
            "body": "Finish this, hit Done on To-Do, then take the next one. Keep shop work ahead of dashboard tinkering.",
            "station": "missions",
            "cta": "Open To-Do",
        }
    if missing_copy:
        return {
            "eyebrow": "Do this next",
            "title": "Write listing copy for a ready design",
            "body": _humanize_mission(missing_copy[0]),
            "station": "pipeline",
            "cta": "Open Queue",
        }
    if ready:
        return {
            "eyebrow": "Do this next",
            "title": "List a design that’s ready",
            "body": _humanize_mission(ready[0]),
            "station": "pipeline",
            "cta": "Open Queue",
        }
    if blocked:
        return {
            "eyebrow": "Blocked",
            "title": "Something in the queue can’t list yet",
            "body": _humanize_mission(blocked[0]),
            "station": "pipeline",
            "cta": "Open Queue",
        }
    return {
        "eyebrow": "You’re clear",
        "title": "No urgent shop jobs in the files",
        "body": "Log new sales on Home when they happen. Refresh ads stats when Etsy numbers change.",
        "station": "hq",
        "cta": "Open Home",
    }


def _humanize_mission(text: str) -> str:
    """Strip markdown/code ticks so missions read like normal English."""
    text = _strip_md(text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = text.replace(" → ", " — ")
    return text.strip()


def _build_cursor_prompt(
    missions: list[str],
    ready: list[str],
    missing_copy: list[str],
    blocked: list[str],
    orders: int,
    units: int,
) -> str:
    lines = [
        "You are the CozyOrbitPrints shop advisor. Read designs/listings/COZY_ORBIT_HANDOFF.md, designs/listings/SHOP_STATE.md, and sales_log.csv first.",
        f"Shop snapshot: {orders} net orders, {units} units logged.",
        "",
        "Tonight's missions:",
    ]
    for i, m in enumerate(missions, 1):
        lines.append(f"{i}. {m}")
    if ready:
        lines.append("")
        lines.append("Ready to list:")
        lines.extend(f"- {x}" for x in ready[:5])
    if missing_copy:
        lines.append("")
        lines.append("Needs listing copy:")
        lines.extend(f"- {x}" for x in missing_copy[:5])
    if blocked:
        lines.append("")
        lines.append("Blocked:")
        lines.extend(f"- {x}" for x in blocked)
    lines.append("")
    lines.append("Help me execute the top mission. Keep changes local-file based (no Etsy API, no OpenAI generate scripts unless I confirm spend).")
    return "\n".join(lines)


def render_html(data: dict) -> str:
    payload = json.dumps(data, ensure_ascii=False)
    # Prevent </script> breakouts from notes text
    payload = payload.replace("<", "\\u003c").replace(">", "\\u003e")
    return HTML_TEMPLATE.replace("__DATA_JSON__", payload)

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>CozyOrbit Shop HQ</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet" />
  <style>
    :root {
      --asphalt: #121416;
      --pit: #1c1f24;
      --steel: #9aa3ad;
      --fog: #c8ced4;
      --line: rgba(245, 197, 24, 0.28);
      --yellow: #f5c518;
      --amber: #e0a100;
      --green: #3dd68c;
      --red: #ff4d4d;
      --warn: #ff9f43;
    }
    * { box-sizing: border-box; }
    html, body { height: 100%; }
    body {
      margin: 0;
      color: var(--fog);
      font-family: "Rajdhani", sans-serif;
      background:
        radial-gradient(ellipse 90% 55% at 50% -8%, rgba(245,197,24,0.11), transparent 50%),
        linear-gradient(180deg, #0e1013 0%, var(--asphalt) 50%, #0a0b0d 100%);
    }
    body::before {
      content: "";
      position: fixed; inset: 0;
      background-image:
        linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px);
      background-size: 48px 48px;
      mask-image: radial-gradient(ellipse at center, black 25%, transparent 78%);
      pointer-events: none; z-index: 0;
    }
    .stage {
      position: relative; z-index: 1;
      max-width: 1180px; margin: 0 auto;
      padding: 18px 22px 20px;
      display: grid; gap: 12px;
      min-height: 100vh;
      grid-template-rows: auto auto auto 1fr auto;
    }
    header.top {
      display: flex; justify-content: space-between; gap: 16px; flex-wrap: wrap;
      align-items: flex-end;
      border-bottom: 1px solid var(--line);
      padding-bottom: 12px;
      animation: rise .6s ease both;
    }
    .brand .mark {
      font-size: clamp(26px, 4vw, 38px);
      font-weight: 700; letter-spacing: .06em;
      text-transform: uppercase; color: var(--yellow); line-height: 1;
    }
    .brand .tag {
      margin-top: 4px;
      font-family: "IBM Plex Mono", monospace;
      font-size: 11px; letter-spacing: .12em; text-transform: uppercase; color: var(--steel);
    }
    .meters { display: flex; gap: 14px; flex-wrap: wrap; }
    .meter { text-align: right; min-width: 70px; }
    .meter b { display: block; font-size: 20px; color: #fff; }
    .meter span {
      font-family: "IBM Plex Mono", monospace;
      font-size: 10px; letter-spacing: .1em; text-transform: uppercase; color: var(--steel);
    }
    .coach {
      display: grid; grid-template-columns: 1fr auto; gap: 14px; align-items: center;
      padding: 14px 16px;
      border: 1px solid var(--line);
      border-left: 4px solid var(--yellow);
      background: rgba(245,197,24,0.07);
      animation: rise .7s .05s ease both;
    }
    .coach .eyebrow {
      font-family: "IBM Plex Mono", monospace;
      font-size: 10px; letter-spacing: .14em; text-transform: uppercase; color: var(--yellow);
    }
    .coach h2 {
      margin: 4px 0 0; font-size: clamp(18px, 2.4vw, 24px); color: #fff; line-height: 1.25; font-weight: 700;
    }
    .coach p { margin: 6px 0 0; color: var(--steel); font-size: 15px; max-width: 62ch; line-height: 1.4; }
    .coach .cta {
      appearance: none; border: 1px solid var(--yellow);
      background: var(--yellow); color: #111;
      font-family: "Rajdhani", sans-serif; font-weight: 700; font-size: 15px;
      letter-spacing: .06em; text-transform: uppercase;
      padding: 12px 16px; cursor: pointer; white-space: nowrap;
    }
    .coach .cta:hover { filter: brightness(1.05); }
    .howto {
      display: flex; gap: 12px; align-items: flex-start; justify-content: space-between;
      padding: 10px 12px;
      border: 1px dashed rgba(154,163,173,0.35);
      background: rgba(255,255,255,0.03);
      font-size: 14px; color: var(--fog);
      animation: rise .7s .08s ease both;
    }
    .howto strong { color: var(--yellow); }
    .howto button {
      appearance: none; border: 0; background: transparent; color: var(--steel);
      font-family: "IBM Plex Mono", monospace; font-size: 11px; letter-spacing: .08em;
      text-transform: uppercase; cursor: pointer; white-space: nowrap;
    }
    .howto.hidden { display: none; }
    .xp-wrap { animation: rise .75s .05s ease both; }
    .xp-label {
      display: flex; justify-content: space-between;
      font-family: "IBM Plex Mono", monospace;
      font-size: 10px; letter-spacing: .1em; text-transform: uppercase; color: var(--steel);
      margin-bottom: 4px;
    }
    .xp-bar {
      height: 8px; background: rgba(255,255,255,0.08);
      border: 1px solid rgba(245,197,24,0.25); overflow: hidden;
    }
    .xp-bar > i {
      display: block; height: 100%; width: 0%;
      background: linear-gradient(90deg, var(--amber), var(--yellow));
      transition: width .45s ease;
    }
    .map-wrap {
      display: grid; grid-template-columns: 1.15fr 0.85fr; gap: 14px;
      animation: rise .85s .1s ease both; align-items: start;
    }
    .map {
      position: relative; min-height: 360px;
      display: grid; place-items: center;
      border: 1px solid rgba(255,255,255,0.06);
      background: rgba(0,0,0,0.18);
      padding: 18px 12px 28px;
    }
    .ring {
      position: absolute; width: min(70%, 420px); aspect-ratio: 1;
      border: 1px dashed rgba(245,197,24,0.16); border-radius: 50%; pointer-events: none;
    }
    .ring.inner {
      width: min(42%, 240px); border-style: solid; border-color: rgba(245,197,24,0.1);
      animation: spin 50s linear infinite;
    }
    .hub {
      position: relative; z-index: 2;
      width: min(180px, 46%); aspect-ratio: 1; border-radius: 50%;
      border: 2px solid var(--yellow);
      background: radial-gradient(circle at 35% 30%, rgba(245,197,24,0.2), transparent 50%), var(--pit);
      display: grid; place-items: center; text-align: center; padding: 12px;
      cursor: pointer; transition: transform .2s ease, box-shadow .2s;
    }
    .hub:hover, .hub.active {
      transform: scale(1.04);
      box-shadow: 0 0 0 5px rgba(245,197,24,0.12);
    }
    .hub .k {
      font-size: 10px; letter-spacing: .16em; color: var(--yellow);
      font-family: "IBM Plex Mono", monospace;
    }
    .hub .v { font-size: clamp(26px, 4vw, 36px); font-weight: 700; color: #fff; line-height: 1; }
    .hub .s { font-size: 13px; color: var(--steel); margin-top: 4px; }
    .stations {
      position: absolute; inset: 10% 3% 8%;
      display: grid; grid-template-columns: 1fr 1fr; gap: 8px;
      align-content: space-between; pointer-events: none;
    }
    .station {
      pointer-events: auto;
      position: relative;
      padding: 12px 12px 10px;
      background: rgba(28,31,36,0.95);
      border: 1px solid rgba(154,163,173,0.28);
      border-left: 3px solid var(--steel);
      cursor: pointer; text-align: left;
      transition: transform .15s, border-color .15s, background .15s;
    }
    .station:hover, .station.active {
      transform: translateY(-2px);
      border-color: var(--yellow);
      background: rgba(36,40,48,0.98);
    }
    .station .name { font-size: 18px; font-weight: 700; letter-spacing: .06em; color: #fff; }
    .station .hint { font-size: 13px; color: var(--steel); margin-top: 2px; }
    .station .sub {
      font-family: "IBM Plex Mono", monospace;
      font-size: 11px; color: var(--fog); margin-top: 6px; opacity: .85;
    }
    .station .dot {
      position: absolute; top: 12px; right: 12px;
      width: 8px; height: 8px; border-radius: 50%; background: var(--steel);
    }
    .station .xp-mini { margin-top: 8px; height: 3px; background: rgba(255,255,255,0.08); }
    .station .xp-mini > i { display: block; height: 100%; background: var(--yellow); }
    .station[data-health="ok"] { border-left-color: var(--green); }
    .station[data-health="ok"] .dot { background: var(--green); box-shadow: 0 0 8px var(--green); }
    .station[data-health="warn"] { border-left-color: var(--warn); }
    .station[data-health="warn"] .dot { background: var(--warn); box-shadow: 0 0 8px var(--warn); }
    .station[data-health="cold"] { border-left-color: var(--red); }
    .station[data-health="cold"] .dot { background: var(--red); box-shadow: 0 0 8px var(--red); }
    .station[data-health="hot"] { border-left-color: var(--yellow); }
    .station[data-health="hot"] .dot { background: var(--yellow); box-shadow: 0 0 10px var(--yellow); }
    .side-rail {
      display: grid; gap: 12px; align-content: start;
    }
    .panel-box {
      padding: 14px;
      border: 1px solid rgba(255,255,255,0.08);
      background: rgba(0,0,0,0.22);
    }
    .panel-title {
      font-family: "IBM Plex Mono", monospace;
      font-size: 10px; letter-spacing: .14em; text-transform: uppercase;
      color: var(--yellow); margin: 0 0 10px;
    }
    .legend { display: grid; gap: 6px; font-size: 13px; color: var(--steel); }
    .legend span { display: inline-flex; align-items: center; gap: 8px; }
    .legend i {
      width: 8px; height: 8px; border-radius: 50%; display: inline-block;
    }
    .legend .g { background: var(--green); }
    .legend .y { background: var(--warn); }
    .legend .r { background: var(--red); }
    .legend .h { background: var(--yellow); }
    .missions-list { display: grid; gap: 8px; }
    .mission-row {
      display: grid; grid-template-columns: 28px 1fr auto; gap: 8px; align-items: start;
      padding: 10px; background: rgba(245,197,24,0.06); border-left: 2px solid var(--yellow);
    }
    .mission-row.done { opacity: .55; border-left-color: var(--green); }
    .mission-row.done .t { text-decoration: line-through; }
    .mission-row .n {
      font-family: "IBM Plex Mono", monospace; color: var(--yellow); font-weight: 600; font-size: 13px;
    }
    .mission-row .t { font-size: 15px; line-height: 1.3; color: #fff; }
    .console {
      border-top: 1px solid var(--line); padding-top: 14px;
      animation: rise .9s .12s ease both; min-height: 240px;
    }
    .detail h2 {
      margin: 0 0 4px; font-size: 26px; font-weight: 700; letter-spacing: .03em; color: #fff;
    }
    .detail .note { margin: 0 0 14px; color: var(--steel); font-size: 15px; max-width: 60ch; line-height: 1.4; }
    .rows { display: grid; gap: 6px; }
    .row {
      display: grid; grid-template-columns: 1fr auto auto auto; gap: 10px; align-items: center;
      padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.06);
      font-family: "IBM Plex Mono", monospace; font-size: 12px;
    }
    .row .name { color: #fff; font-family: "Rajdhani", sans-serif; font-size: 16px; font-weight: 600; }
    .row .muted { color: var(--steel); }
    .pill {
      display: inline-block; padding: 2px 8px; font-size: 11px;
      letter-spacing: .08em; text-transform: uppercase; border: 1px solid currentColor;
    }
    .pill.ok { color: var(--green); }
    .pill.warn { color: var(--warn); }
    .pill.cold { color: var(--red); }
    .pill.hot { color: var(--yellow); }
    .stat-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 14px; }
    .stat { padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.08); }
    .stat b { display: block; font-size: 22px; color: #fff; }
    .stat span {
      font-family: "IBM Plex Mono", monospace; font-size: 10px;
      letter-spacing: .1em; text-transform: uppercase; color: var(--steel);
    }
    .btn {
      appearance: none; border: 1px solid var(--yellow);
      background: rgba(245,197,24,0.12); color: var(--yellow);
      font-family: "Rajdhani", sans-serif; font-weight: 700; font-size: 15px;
      letter-spacing: .06em; text-transform: uppercase;
      padding: 10px 14px; cursor: pointer; margin-top: 10px;
    }
    .btn.tiny { padding: 6px 10px; font-size: 12px; margin-top: 0; }
    .btn:hover { background: rgba(245,197,24,0.22); }
    .btn.copied { border-color: var(--green); color: var(--green); }
    .btn:disabled { opacity: .4; cursor: not-allowed; }
    .btn.primary { background: var(--yellow); color: #111; }
    .empty { color: var(--steel); font-size: 15px; }
    .help-line {
      font-size: 13px; color: var(--steel); margin: 0 0 12px; line-height: 1.4;
    }
    .sale-form {
      display: grid; grid-template-columns: 1fr 1fr; gap: 10px 12px;
      margin: 4px 0 8px; padding: 12px;
      border: 1px solid rgba(245,197,24,0.22); background: rgba(245,197,24,0.04);
    }
    .sale-form label {
      display: grid; gap: 4px;
      font-family: "IBM Plex Mono", monospace;
      font-size: 10px; letter-spacing: .1em; text-transform: uppercase; color: var(--steel);
    }
    .sale-form label.wide { grid-column: 1 / -1; }
    .sale-form input, .sale-form select {
      appearance: none; width: 100%; padding: 8px 10px;
      border: 1px solid rgba(154,163,173,0.35);
      background: rgba(12,14,18,0.9); color: #fff;
      font-family: "Rajdhani", sans-serif; font-size: 15px;
    }
    .sale-form input:focus, .sale-form select:focus { outline: none; border-color: var(--yellow); }
    .sale-form .actions {
      grid-column: 1 / -1; display: flex; gap: 10px; align-items: center; flex-wrap: wrap;
    }
    .sale-form .btn { margin-top: 0; }
    .sale-form .optional { display: none; }
    .sale-form.show-more .optional { display: grid; }
    .keys {
      font-family: "IBM Plex Mono", monospace; font-size: 10px;
      color: var(--steel); letter-spacing: .05em; margin-top: 8px;
    }
    .live {
      display: inline-flex; align-items: center; gap: 6px;
      font-family: "IBM Plex Mono", monospace; font-size: 10px;
      letter-spacing: .12em; text-transform: uppercase; color: var(--steel); margin-top: 8px;
    }
    .live .pulse { width: 7px; height: 7px; border-radius: 50%; background: var(--steel); }
    .live.on .pulse {
      background: var(--green); box-shadow: 0 0 10px var(--green);
      animation: pulse 1.6s ease-in-out infinite;
    }
    footer.stamp {
      font-family: "IBM Plex Mono", monospace; font-size: 11px; color: var(--steel);
      display: flex; justify-content: space-between; gap: 12px; flex-wrap: wrap; opacity: .9;
      border-top: 1px solid rgba(255,255,255,0.06); padding-top: 10px;
    }
    footer a { color: var(--yellow); text-decoration: none; }
    .toast {
      position: fixed; top: 16px; right: 16px; z-index: 50;
      min-width: 220px; max-width: min(340px, 92vw); padding: 12px 14px;
      background: rgba(28,31,36,0.97); border: 1px solid var(--yellow); border-left: 3px solid var(--yellow);
      box-shadow: 0 16px 40px rgba(0,0,0,.45);
      transform: translateY(-120%); opacity: 0;
      transition: transform .35s ease, opacity .35s ease; pointer-events: none;
    }
    .toast.show { transform: translateY(0); opacity: 1; }
    .toast .k {
      font-family: "IBM Plex Mono", monospace; font-size: 10px;
      letter-spacing: .14em; color: var(--yellow); text-transform: uppercase;
    }
    .toast .t { margin-top: 4px; font-size: 15px; font-weight: 600; color: #fff; line-height: 1.25; }
    @keyframes rise {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: .35; } }
    @media (max-width: 900px) {
      .map-wrap { grid-template-columns: 1fr; }
      .stations { position: relative; inset: auto; margin-top: 14px; }
      .ring, .ring.inner { display: none; }
      .map { min-height: auto; }
      .hub { margin: 0 auto; }
      .stat-grid { grid-template-columns: 1fr 1fr; }
      .coach { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="stage">
    <div class="toast" id="toast" role="status" aria-live="polite">
      <div class="k" id="toast-k">Update</div>
      <div class="t" id="toast-t"></div>
    </div>

    <header class="top">
      <div class="brand">
        <div class="mark">CozyOrbit Shop HQ</div>
        <div class="tag">Simple shop monitor · local files only</div>
      </div>
      <div class="meters" id="meters"></div>
    </header>

    <section class="coach" id="coach">
      <div>
        <div class="eyebrow" id="coach-eyebrow">Do this next</div>
        <h2 id="coach-title">—</h2>
        <p id="coach-body"></p>
      </div>
      <button type="button" class="cta" id="coach-cta">Open</button>
    </section>

    <div class="howto" id="howto">
      <div>
        <strong>How to use:</strong>
        Press <strong>1–6</strong> (or tap a station) · yellow banner = your next job ·
        <strong>Home</strong> logs sales · <strong>To-Do</strong> marks jobs done.
        Needs <strong>--serve</strong> for live logging.
      </div>
      <button type="button" id="howto-dismiss">Got it</button>
    </div>

    <div class="xp-wrap">
      <div class="xp-label">
        <span id="xp-label-text">Shop level progress</span>
        <span id="xp-label-nums">0/5</span>
      </div>
      <div class="xp-bar"><i id="xp-fill"></i></div>
    </div>

    <div class="map-wrap">
      <section class="map" aria-label="Stations">
        <div class="ring"></div>
        <div class="ring inner"></div>
        <button class="hub" id="hub" type="button" data-station="hq" aria-label="Home">
          <div>
            <div class="k">ORDERS</div>
            <div class="v" id="hub-orders">—</div>
            <div class="s" id="hub-units">— shirts sold</div>
          </div>
        </button>
        <div class="stations" id="stations"></div>
      </section>

      <aside class="side-rail">
        <div class="panel-box">
          <p class="panel-title">Tonight’s to-do</p>
          <div class="missions-list" id="missions"></div>
          <button type="button" class="btn" id="copy-prompt">Copy help prompt</button>
          <p class="keys">1 Home · 2 Etsy · 3 eBay · 4 Ads · 5 Queue · 6 To-Do</p>
          <p class="live" id="live"><span class="pulse" aria-hidden="true"></span><span class="live-text">Snapshot</span></p>
        </div>
        <div class="panel-box">
          <p class="panel-title">Status colors</p>
          <div class="legend">
            <span><i class="g"></i> Green — healthy</span>
            <span><i class="y"></i> Yellow — needs a look</span>
            <span><i class="r"></i> Red — problem / empty</span>
            <span><i class="h"></i> Gold — priority / to-do</span>
          </div>
          <p class="help-line" id="glossary-roas" style="margin-top:10px"></p>
        </div>
      </aside>
    </div>

    <section class="console">
      <div class="detail">
        <p class="panel-title" id="panel-kicker">Station</p>
        <h2 id="panel-title">Home</h2>
        <p class="note" id="panel-note"></p>
        <div id="panel-body"></div>
      </div>
    </section>

    <footer class="stamp">
      <span id="stamp"></span>
      <a id="shop-link" href="#" target="_blank" rel="noopener">Open Etsy shop ↗</a>
    </footer>
  </div>

  <script id="tycoon-data" type="application/json">__DATA_JSON__</script>
  <script>
    let DATA = JSON.parse(document.getElementById("tycoon-data").textContent);
    let activeStation = "hq";
    let lastSaleKey = DATA.latest_sale_key || "";
    let toastTimer = null;
    const isLive = () => location.protocol.startsWith("http");
    const ORDER = ["hq", "etsy", "ebay", "ads", "pipeline", "missions"];

    const money = (n) => {
      if (n == null || Number.isNaN(n)) return "—";
      return "$" + Number(n).toLocaleString(undefined, { maximumFractionDigits: 2 });
    };

    function escapeHtml(str) {
      return String(str)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;");
    }

    function renderCoach() {
      const c = DATA.coach || {};
      document.getElementById("coach-eyebrow").textContent = c.eyebrow || "Next";
      document.getElementById("coach-title").textContent = c.title || "—";
      document.getElementById("coach-body").textContent = c.body || "";
      const cta = document.getElementById("coach-cta");
      cta.textContent = c.cta || "Open";
      cta.onclick = () => showStation(c.station || "hq");
    }

    function renderXp() {
      const s = DATA.snapshot;
      document.getElementById("xp-label-text").textContent =
        `Shop level ${s.level} → ${Number(s.level) + 1} (every ${s.xp_to_next || 5} orders)`;
      document.getElementById("xp-label-nums").textContent =
        `${s.xp_into_level || 0} / ${s.xp_to_next || 5}`;
      document.getElementById("xp-fill").style.width = (s.xp_pct || 0) + "%";
    }

    function renderMeters() {
      const s = DATA.snapshot;
      document.getElementById("meters").innerHTML = [
        ["DAY", s.shop_day || "—"],
        ["LEVEL", s.level || "—"],
        ["ORDERS", s.orders],
        ["SHIRTS", s.units],
        ["SALES $", money(s.revenue)],
        ["AFTER PRINT", money(s.gross_after_printify)],
      ].map(([k,v]) => `<div class="meter"><b>${v}</b><span>${k}</span></div>`).join("");
      document.getElementById("hub-orders").textContent = s.orders;
      document.getElementById("hub-units").textContent = s.units + " shirts logged";
      renderXp();
    }

    function renderStations() {
      // Keep hub separate; show other 5 + make hub also a station feel via keys
      const html = DATA.stations
        .filter(s => s.id !== "hq")
        .map(s => `
          <button type="button" class="station" data-station="${s.id}" data-health="${s.health}">
            <span class="dot" aria-hidden="true"></span>
            <div class="name">${escapeHtml(s.name || s.label)}</div>
            <div class="hint">${escapeHtml(s.hint || "")}</div>
            <div class="sub">${escapeHtml(s.sub || "")}</div>
            <div class="xp-mini"><i style="width:${s.xp || 0}%"></i></div>
          </button>`).join("");
      document.getElementById("stations").innerHTML = html;
    }

    function missionItemsHtml() {
      const rich = DATA.missions_rich || DATA.missions.map(t => ({ text: t, display: t, done: false }));
      return rich.map((m, i) => {
        const text = m.display || m.text || m;
        const done = !!m.done;
        const btn = done
          ? `<span class="pill ok">done</span>`
          : `<button type="button" class="btn tiny" data-mission-done="${i}" ${isLive() ? "" : "disabled"}>Done</button>`;
        return `<div class="mission-row ${done ? "done" : ""}">
          <span class="n">0${i+1}</span>
          <span class="t">${escapeHtml(text)}</span>
          ${btn}
        </div>`;
      }).join("");
    }

    function bindMissionButtons(root) {
      root.querySelectorAll("[data-mission-done]").forEach(btn => {
        btn.addEventListener("click", () => markMissionDone(Number(btn.getAttribute("data-mission-done"))));
      });
    }

    function renderMissions() {
      const el = document.getElementById("missions");
      el.innerHTML = missionItemsHtml() || `<p class="empty">Nothing queued.</p>`;
      bindMissionButtons(el);
    }

    function setActive(id) {
      activeStation = id;
      document.querySelectorAll("[data-station]").forEach(el => {
        el.classList.toggle("active", el.getAttribute("data-station") === id);
      });
      const meta = DATA.stations.find(s => s.id === id);
      document.getElementById("panel-kicker").textContent =
        `Station ${ORDER.indexOf(id) + 1} of 6 · ${meta ? (meta.name || meta.label) : id}`;
    }

    function showStation(id) {
      setActive(id);
      const body = document.getElementById("panel-body");
      const title = document.getElementById("panel-title");
      const note = document.getElementById("panel-note");

      if (id === "hq") {
        title.textContent = "Home";
        note.textContent = "Big numbers for the whole shop. Log a new sale here when something sells.";
        const today = new Date().toISOString().slice(0, 10);
        const suggestions = (DATA.listing_suggestions || [])
          .map(n => `<option value="${escapeHtml(n)}"></option>`).join("");
        const recent = DATA.recent_sales.slice(0, 6).map(r => `
          <div class="row">
            <span class="name">${escapeHtml(r.date)} · ${escapeHtml(r.listing)}</span>
            <span class="muted">${escapeHtml(r.market)}</span>
            <span class="muted">${money(r.revenue)}</span>
            <span class="muted">${r.qty}u</span>
          </div>`).join("");
        body.innerHTML = `
          <div class="stat-grid">
            <div class="stat"><b>${money(DATA.snapshot.revenue)}</b><span>Item sales $</span></div>
            <div class="stat"><b>${money(DATA.snapshot.printify)}</b><span>Printify costs</span></div>
            <div class="stat"><b>${money(DATA.snapshot.gross_after_printify)}</b><span>Left after Printify</span></div>
          </div>
          <p class="help-line">${escapeHtml((DATA.glossary && DATA.glossary.printify) || "")}</p>
          <p class="panel-title">Log a sale</p>
          <p class="help-line">${isLive()
            ? "Fill the basics, then Save. Extra fields are optional."
            : "Start the live server to save from this form: python scripts/build_tycoon_hq.py --serve"}</p>
          <form class="sale-form" id="sale-form">
            <label>Date<input name="order_date" type="date" value="${today}" required></label>
            <label>Where sold
              <select name="marketplace" required>
                <option value="Etsy">Etsy</option>
                <option value="eBay">eBay</option>
              </select>
            </label>
            <label class="wide">What sold
              <input name="listing" list="listing-suggestions" required placeholder="Start typing a listing name…">
              <datalist id="listing-suggestions">${suggestions}</datalist>
            </label>
            <label>How many<input name="qty" type="number" min="1" step="1" value="1" required></label>
            <label>Price you charged<input name="item_price" type="number" min="0" step="0.01" placeholder="26.09"></label>
            <div class="actions">
              <button type="submit" class="btn primary" ${isLive() ? "" : "disabled"}>Save sale</button>
              <button type="button" class="btn" id="toggle-more">More details</button>
              <span class="empty" id="sale-form-status">${isLive() ? "Saves to sales_log.csv" : "Live server required"}</span>
            </div>
            <label class="optional">Printify cost<input name="printify_cost" type="number" min="0" step="0.01"></label>
            <label class="optional">Your profit est.<input name="est_net_profit" type="number" step="0.01"></label>
            <label class="optional">Traffic
              <input name="traffic_source" list="traffic-suggestions" placeholder="Organic / Ads">
              <datalist id="traffic-suggestions">
                <option value="Organic"></option>
                <option value="Etsy Ads"></option>
                <option value="eBay promoted listing"></option>
                <option value="Unknown"></option>
              </datalist>
            </label>
            <label class="optional">Color<input name="shirt_color"></label>
            <label class="optional">Size<input name="size"></label>
            <label class="optional">Order ID<input name="order_id"></label>
            <label class="optional">Buyer<input name="buyer"></label>
            <label class="optional wide">Notes<input name="notes"></label>
          </form>
          <p class="panel-title" style="margin-top:16px">Recent sales</p>
          <div class="rows">${recent || '<p class="empty">No sales logged yet.</p>'}</div>`;
        const form = document.getElementById("sale-form");
        form?.addEventListener("submit", submitSaleLog);
        document.getElementById("toggle-more")?.addEventListener("click", () => {
          form.classList.toggle("show-more");
          const open = form.classList.contains("show-more");
          document.getElementById("toggle-more").textContent = open ? "Hide details" : "More details";
        });
        return;
      }

      if (id === "etsy" || id === "ebay") {
        const m = DATA.markets[id];
        title.textContent = id === "etsy" ? "Etsy" : "eBay";
        note.textContent = id === "etsy"
          ? "Your main marketplace. Yellow C5 was taken down on Etsy for IP — don’t relist the CORVETTE wordmark art."
          : "Newer channel that’s converting. Watch promoted fees on cheap tees.";
        const sales = DATA.recent_sales.filter(r => r.market.toLowerCase() === id);
        body.innerHTML = `
          <div class="stat-grid">
            <div class="stat"><b>${m.orders}</b><span>Orders</span></div>
            <div class="stat"><b>${m.units}</b><span>Shirts</span></div>
            <div class="stat"><b>${money(m.revenue)}</b><span>Sales $</span></div>
          </div>
          <p class="help-line">${escapeHtml(m.note || "")}</p>
          <p class="panel-title">Sales here</p>
          ${sales.length ? `<div class="rows">${sales.map(r => `
            <div class="row">
              <span class="name">${escapeHtml(r.date)} · ${escapeHtml(r.listing)}</span>
              <span class="muted">${escapeHtml(r.color || "—")}</span>
              <span class="muted">${money(r.revenue)}</span>
              <span class="muted">${escapeHtml(r.source || "")}</span>
            </div>`).join("")}</div>` : `<p class="empty">No sales on this channel yet.</p>`}`;
        return;
      }

      if (id === "ads") {
        title.textContent = "Ads";
        note.textContent = DATA.ads.stale
          ? "These ad numbers are old. Until you paste a fresh snapshot into SHOP_STATE, treat this as a reminder — not today’s truth."
          : "ROAS shows how much sales you get per $1 of ad spend.";
        const rows = DATA.ads.rows || [];
        const banner = DATA.ads.stale
          ? `<p class="pill warn" style="margin-bottom:12px">Update needed · ${DATA.ads.age_days} days old (${escapeHtml(DATA.ads.snapshot_date || "?")})</p>`
          : `<p class="help-line">${escapeHtml((DATA.glossary && DATA.glossary.roas) || "")}</p>`;
        body.innerHTML = banner + (rows.length ? `<div class="rows">${rows.map(r => `
          <div class="row">
            <span class="name">${escapeHtml(r.listing)}</span>
            <span class="muted">${escapeHtml(r.views)} views</span>
            <span class="pill ${r.health}">${escapeHtml(r.roas)}× back</span>
            <span class="muted">${escapeHtml(r.orders)} orders</span>
          </div>`).join("")}</div>` : `<p class="empty">No ads table found in SHOP_STATE yet.</p>`);
        return;
      }

      if (id === "pipeline") {
        const p = DATA.pipeline;
        title.textContent = "Queue";
        note.textContent = "Designs waiting to go live. Ready = file + listing copy. Needs copy = write the .md. Blocked = don’t list yet.";
        const block = (label, items, cls, empty) => `
          <p class="panel-title">${label} <span class="pill ${cls}">${items.length}</span></p>
          ${items.length ? `<div class="rows">${items.map(t => `
            <div class="row"><span class="name" style="grid-column:1/-1">${escapeHtml(t.replace(/`/g, ""))}</span></div>`).join("")}</div>`
            : `<p class="empty">${empty}</p>`}`;
        body.innerHTML = [
          block("Ready to list", p.ready, "ok", "Nothing ready — nice, or time to finish copy."),
          block("Needs listing copy", p.needs_copy, "warn", "No copy gaps."),
          block("Blocked", p.blocked, "cold", "Nothing blocked."),
          block("Shop checklist", p.checklist, "warn", "Checklist clear."),
        ].join("");
        return;
      }

      if (id === "missions") {
        title.textContent = "To-Do";
        note.textContent = "Your next three shop jobs from the daily brief. Mark Done (live server) to save a note in SHOP_STATE.";
        const log = (DATA.mission_log || []).slice().reverse().map(r => `
          <div class="row">
            <span class="name">${escapeHtml(r.when)}</span>
            <span class="muted" style="grid-column:2/-1">${escapeHtml(r.mission)}</span>
          </div>`).join("");
        body.innerHTML = `
          <div class="missions-list" id="missions-panel">${missionItemsHtml()}</div>
          <button type="button" class="btn" id="copy-prompt-main">Copy help prompt for Cursor</button>
          <p class="help-line" style="margin-top:10px">This copies a ready-made message you can paste into Cursor so I can help with the top job.</p>
          <p class="panel-title" style="margin-top:16px">Finished recently</p>
          <div class="rows">${log || '<p class="empty">No finished jobs logged yet.</p>'}</div>`;
        document.getElementById("copy-prompt-main")?.addEventListener("click", copyPrompt);
        bindMissionButtons(document.getElementById("missions-panel"));
      }
    }

    async function submitSaleLog(e) {
      e.preventDefault();
      if (!isLive()) {
        showToast("Start live mode", "Run: python scripts/build_tycoon_hq.py --serve");
        return;
      }
      const form = e.target;
      const status = document.getElementById("sale-form-status");
      const payload = Object.fromEntries(new FormData(form).entries());
      status.textContent = "Saving…";
      try {
        const res = await fetch("/api/sale-log", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "Failed");
        status.textContent = "Saved ✓";
        showToast(`Sale · ${payload.marketplace}`, `${payload.listing} · qty ${payload.qty}`);
        form.reset();
        form.order_date.value = new Date().toISOString().slice(0, 10);
        form.qty.value = "1";
        form.classList.remove("show-more");
        setTimeout(pollLive, 500);
      } catch (err) {
        status.textContent = String(err.message || err);
        showToast("Couldn’t save", String(err.message || err));
      }
    }

    async function markMissionDone(index) {
      if (!isLive()) {
        showToast("Start live mode", "Done buttons need --serve");
        return;
      }
      const rich = DATA.missions_rich || [];
      const mission = (rich[index] && rich[index].text) || DATA.missions[index];
      if (!mission) return;
      try {
        const res = await fetch("/api/mission-done", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ mission }),
        });
        const payload = await res.json();
        if (!res.ok) throw new Error(payload.error || "Failed");
        showToast("Marked done", rich[index]?.display || mission);
        setTimeout(pollLive, 500);
      } catch (err) {
        showToast("Couldn’t log", String(err.message || err));
      }
    }

    function showToast(kicker, text) {
      const el = document.getElementById("toast");
      document.getElementById("toast-k").textContent = kicker;
      document.getElementById("toast-t").textContent = text;
      el.classList.add("show");
      clearTimeout(toastTimer);
      toastTimer = setTimeout(() => el.classList.remove("show"), 4200);
    }

    async function copyPrompt() {
      const text = DATA.cursor_prompt || "";
      try { await navigator.clipboard.writeText(text); }
      catch (_) {
        const ta = document.createElement("textarea");
        ta.value = text; document.body.appendChild(ta); ta.select();
        document.execCommand("copy"); ta.remove();
      }
      document.querySelectorAll("#copy-prompt, #copy-prompt-main").forEach(btn => {
        if (!btn) return;
        btn.classList.add("copied");
        const old = btn.textContent;
        btn.textContent = "Copied ✓";
        setTimeout(() => { btn.classList.remove("copied"); btn.textContent = old.includes("Cursor") ? "Copy help prompt for Cursor" : "Copy help prompt"; }, 1400);
      });
    }

    function updateStamp() {
      const live = isLive();
      const stale = DATA.ads && DATA.ads.stale ? " · ads need refresh" : "";
      document.getElementById("stamp").textContent =
        `Updated ${DATA.generated_at}${stale}` +
        (live ? " · live" : " · open with --serve for saving");
      document.getElementById("shop-link").href = DATA.shop_url;
      const liveEl = document.getElementById("live");
      liveEl.classList.toggle("on", live);
      liveEl.querySelector(".live-text").textContent = live ? "Live — saves work" : "Snapshot only";
      const g = DATA.glossary || {};
      document.getElementById("glossary-roas").textContent = g.roas || "";
    }

    function maybeToastSale(prevKey, next) {
      const key = next.latest_sale_key || "";
      if (!key || key === prevKey) return;
      const sale = (next.recent_sales || [])[0];
      if (!sale) return;
      showToast(`New sale · ${sale.market}`, `${sale.listing} · ${money(sale.revenue)}`);
    }

    function applyData(next) {
      maybeToastSale(lastSaleKey, next);
      lastSaleKey = next.latest_sale_key || lastSaleKey;
      DATA = next;
      renderAll();
      showStation(activeStation);
    }

    function renderAll() {
      renderMeters();
      renderStations();
      renderMissions();
      renderCoach();
      updateStamp();
    }

    function bind() {
      document.getElementById("stations").addEventListener("click", (e) => {
        const btn = e.target.closest("[data-station]");
        if (btn) showStation(btn.getAttribute("data-station"));
      });
      document.getElementById("hub").addEventListener("click", () => showStation("hq"));
      document.getElementById("copy-prompt").addEventListener("click", copyPrompt);
      document.getElementById("howto-dismiss").addEventListener("click", () => {
        document.getElementById("howto").classList.add("hidden");
        try { localStorage.setItem("cozy_hq_howto_dismissed", "1"); } catch (_) {}
      });
      try {
        if (localStorage.getItem("cozy_hq_howto_dismissed") === "1") {
          document.getElementById("howto").classList.add("hidden");
        }
      } catch (_) {}
      window.addEventListener("keydown", (e) => {
        const n = parseInt(e.key, 10);
        if (n >= 1 && n <= 6) showStation(ORDER[n - 1]);
      });
    }

    async function pollLive() {
      if (!isLive()) return;
      try {
        const res = await fetch("cozy_orbit_tycoon.json?t=" + Date.now(), { cache: "no-store" });
        if (!res.ok) return;
        const next = await res.json();
        if (next.generated_ts && next.generated_ts !== DATA.generated_ts) applyData(next);
      } catch (_) {}
    }

    bind();
    renderAll();
    showStation(DATA.coach && DATA.coach.station ? DATA.coach.station : "hq");
    if (isLive()) setInterval(pollLive, 4000);
  </script>
</body>
</html>
"""




def _source_mtime() -> float:
    times = [0.0]
    for path in WATCH_PATHS:
        if path.exists():
            times.append(path.stat().st_mtime)
    return max(times)


def write_outputs(output: Path, data: dict | None = None) -> dict:
    data = data or build_snapshot()
    html = render_html(data)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")
    json_path = output.with_suffix(".json")
    json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return data


def run_watch(output: Path, interval: float = 2.0) -> None:
    last = -1.0
    print(f"Watching {brief.SALES_LOG.name} + {brief.SHOP_STATE.name} → {output}")
    while True:
        mtime = _source_mtime()
        if mtime != last:
            data = write_outputs(output)
            print(
                f"[{datetime.now().strftime('%H:%M:%S')}] refreshed · "
                f"{data['snapshot']['orders']} orders · ${data['snapshot']['revenue']:.2f}"
                + (" · ADS STALE" if data["ads"].get("stale") else "")
            )
            last = mtime
        time.sleep(interval)


def run_serve(output: Path, port: int = 8765, open_browser: bool = True) -> None:
    write_outputs(output)
    watch = Thread(target=run_watch, args=(output,), daemon=True)
    watch.start()
    root = output.parent

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(root), **kwargs)

        def log_message(self, fmt: str, *args) -> None:
            return

        def _json_response(self, code: int, payload: dict) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self) -> None:  # noqa: N802
            route = self.path.split("?", 1)[0]
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b"{}"
            try:
                payload = json.loads(raw.decode("utf-8") or "{}")
                if route == "/api/mission-done":
                    mission = (payload.get("mission") or "").strip()
                    if not mission:
                        raise ValueError("mission required")
                    entry = log_mission_done(mission)
                    write_outputs(output)
                    self._json_response(200, {"ok": True, "entry": entry})
                    return
                if route == "/api/sale-log":
                    entry = log_sale(payload)
                    write_outputs(output)
                    self._json_response(200, {"ok": True, "entry": entry})
                    return
                self.send_error(404)
            except Exception as exc:  # noqa: BLE001
                self._json_response(400, {"ok": False, "error": str(exc)})

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{port}/{output.name}"
    print(f"Serving Tycoon HQ at {url}", flush=True)
    print("APIs: POST /api/sale-log · POST /api/mission-done", flush=True)
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-o", "--output", type=Path, default=OUT_DEFAULT)
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args()

    if args.serve:
        run_serve(args.output, port=args.port, open_browser=not args.no_open)
        return
    if args.watch:
        run_watch(args.output)
        return

    data = write_outputs(args.output)
    print(f"OK  {args.output}")
    print(f"OK  {args.output.with_suffix('.json')}")
    print(
        f"    {data['snapshot']['orders']} orders · lvl {data['snapshot']['level']} "
        f"({data['snapshot']['xp_into_level']}/{data['snapshot']['xp_to_next']} xp) · "
        f"rev ${data['snapshot']['revenue']:.2f}"
    )
    if data["ads"].get("stale"):
        print(f"    WARN ads stale {data['ads'].get('age_days')}d ({data['ads'].get('snapshot_date')})")
    print("    live: .venv/bin/python scripts/build_tycoon_hq.py --serve")


if __name__ == "__main__":
    main()
