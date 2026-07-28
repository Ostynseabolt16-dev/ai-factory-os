# CozyOrbitPrints / ai-factory-os

> **Live business (Jul 2026):** Corvette graphic tees + hoodies on **Etsy + eBay**, fulfilled by **Printify**.  
> Shop: https://www.etsy.com/shop/CozyOrbitPrints  
> This is **not** a kawaii sticker project. Old May “AI Factory” commits are scaffolding only.

## Phone / any new Cursor session — start here

1. Read **`designs/listings/COZY_ORBIT_HANDOFF.md`**
2. Read **`designs/listings/SHOP_STATE.md`**
3. Read **`sales_log.csv`**
4. Optional: `AI_CONTEXT.md`

Say: `@COZY_ORBIT_HANDOFF.md @SHOP_STATE.md` at the start of a phone chat.

## What changed Jul 16, 2026

- 2 eBay sales: Yellow C5 tee (~breakeven without Printify coupon; ~$10 with $10 coupon) + Yellow C5 2-sided hoodie ($51.99, Printify pending)
- Etsy Yellow C5 listing **taken down** (CORVETTE wordmark IP risk)
- Shop state files are now in git so phone agents stay current

## Repo layout (what matters)

| Path | Purpose |
|------|---------|
| `designs/README.md` | **Folder map** — where McQueen/couple, pickleball, Corvette live |
| `designs/couple_faces/` | Matching race-car face Printify uploads (list tonight) |
| `designs/pickleball/` | Pickleball Printify uploads |
| `designs/corvette/` | Corvette masters (often Mac-local) |
| `designs/listings/SHOP_STATE.md` | Source of truth for ads, sales, strategy |
| `designs/listings/COZY_ORBIT_HANDOFF.md` | Short catch-up for new sessions |
| `designs/listings/COUPLE_RACE_CAR_FACES.md` | Couple face listing copy |
| `sales_log.csv` | Order log |
| `scripts/shop_daily_brief.py` | Local priorities (needs Mac/venv) |
| `ai_factory/` | Old factory code — ignore |

**Deleted Jul 28:** May sticker / cute / `product_*` / social-anxiety art + factory mockups.

## GitHub vs Cursor chats

- **Files** sync via git push/pull — that’s what this README fixes.
- **Chats** under different repos (wealth, credit cards, other Printify threads) stay in those repo workspaces. Opening this repo on phone does **not** load those other chats into the agent automatically.
