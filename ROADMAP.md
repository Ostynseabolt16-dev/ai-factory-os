# AI Factory OS — roadmap

Ordered for **revenue first**, automation second. Ship listings that sell; automate what repeats.

## Phase 0 — Now (foundation)

- [x] OpenAI image generation to disk (`designs/`)
- [x] One-command scripts from project root (`image_creator.py`, etc.)
- [ ] **Product sheet**: one row per design (file path, title, status, Etsy ID) — start with CSV or SQLite
- [ ] **Listing copy**: SEO title + description + tags from templates (manual paste to Etsy/Printify is OK)

## Phase 1 — AI image generation

- [ ] Prompt presets per product line (kawaii, typography, seasonal)
- [ ] Regeneration loop (same idea, new seed / tweak prompt)
- [ ] Cost tracking (tokens/API $ per design)

## Phase 2 — SEO title generation

- [ ] Keyword + niche in → title out (Etsy length limits, no spam)
- [ ] A/B notes in your product DB (which title variant is live)

## Phase 3 — Etsy description + auto tags

- [ ] Structured sections: hook, bullets, care, shipping disclaimer
- [ ] Tag generator from niche + materials + audience (respect Etsy limits)

## Phase 4 — Product database

- [ ] SQLite (single file) or Google Sheet — pick one and stay consistent
- [ ] Fields: `id`, `image_path`, `title`, `description`, `tags`, `status`, `etsy_listing_id`, `created_at`

## Phase 5 — Approval queue

- [ ] Folder or DB status: `draft` → `ready_for_review` → `approved` → `live`
- [ ] Simple CLI or spreadsheet view before anything touches Etsy API

## Phase 6 — Batch generation

- [ ] Read ideas from file → generate N images → enqueue for review
- [ ] Rate limits and resume (stop/start without losing progress)

## Phase 7 — Analytics dashboard

- [ ] Export Etsy stats (manual CSV OK at first) into simple charts
- [ ] Link views/favorites/orders back to design `id`

## Phase 8 — Trend scraping

- [ ] Harden `research/etsy_trends` (respect robots/ToS; prefer official APIs or manual exports when possible)
- [ ] Store “signals” (search terms, competitor titles) for prompt ideas

## Phase 9 — Mockup generation

- [ ] Printify/template assets per SKU; batch apply approved PNGs

---

**Non-goals for v1:** multi-user auth, microservices, perfect UI. Prefer files + CLI until revenue proves the stack.
