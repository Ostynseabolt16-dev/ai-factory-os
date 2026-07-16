# AI Factory OS Context

> **STOP — read this first (updated 2026-07-16)**  
> This repo’s GitHub history still looks like a May **kawaii sticker / factory** project. That is **stale**.  
> **Live business:** **CozyOrbitPrints** — Corvette C3–C8 graphic tees + hoodies on **Etsy + eBay**, fulfilled by **Printify**.  
> **Source of truth (local, often not pushed):** `designs/listings/SHOP_STATE.md`, `designs/listings/COZY_ORBIT_HANDOFF.md`, `sales_log.csv`.  
> Do **not** resume sticker generation, factory CSV sticker pipelines, or Amazon unless the owner explicitly asks.

## Current Architecture
- Local-first Python workflow using CSV-backed state.
- Modular package structure under `ai_factory/`.
- Product lifecycle, listing generation, intelligence scoring, and export pipelines are separated by domain.
- CLI-driven operations via `ai_factory/cli.py`.
- Data flows from product creation → mockup generation → listing readiness → upload/export.

## Completed Systems
- Product lifecycle manager with CSV schema migration in `ai_factory/products/product_manager.py`.
- Trend intelligence and scoring engine in `ai_factory/analytics/trend_engine.py`.
- Etsy upload queue, retry, cleanup, and manual export support in `ai_factory/etsy/etsy_upload.py`.
- Listing packaging and manifest generation in `ai_factory/listings/listing_packager.py`.
- Local-first analytics and scoring engines across `ai_factory/intelligence/`.
- Developer operations CLI commands in `ai_factory/cli.py`.
- Regression tests added for trending and upload queue behavior.

## Etsy Importer Progress
- Etsy importer exists at `ai_factory/importers/etsy_shop_importer.py`.
- Import path supports ingesting existing Etsy listings for analysis.
- Etsy API integration is pending approval; workflows are built to use exported/manual data first.

## Upload Queue System
- Queue persistence via CSV-backed queue in `ai_factory/etsy/etsy_upload.py`.
- Supports queue listing, dry-run validation, retry failed items, cleanup, and manual export packages.
- Prioritization is built to promote high-opportunity and upload-ready products.

## Mockup Pipeline
- Mockups are generated under `mockups/` and orchestrated in `ai_factory/mockups/` modules.
- Listing package generation orders mockups and surfaces image manifest metadata.
- Pipeline is designed to preserve manual export workflows without external APIs.

## CLI Commands
- CLI entry point: `python -m ai_factory.cli`.
- Provides inventory reports, trend scoring, upload queue operations, backups, analytics, and import/export actions.
- New intelligence commands support scoring products and surfacing top opportunity/low-quality listings.

## CSV Schemas
- Primary schema: `products.csv` with safe migration by `ensure_products_csv_schema()`.
- Key fields: product metadata, scoring fields, lifecycle fields, upload priority, and legacy support.
- Additional CSVs include `etsy_upload_log.csv`, `task_queue.csv`, `workflow_history.csv`, and `trend_data.csv`.

## Current Blockers
- Etsy API approval and real upload integration.
- Marketplace adapter expansion beyond Etsy.
- Complete automated trend data ingestion and ranking.
- Dashboard/visualization layer for analytics.

## Future Roadmap
- Add marketplace-agnostic adapters for Shopify, TikTok, Gumroad.
- Build predictive opportunity engine from multi-source trends.
- Add dashboard views and analytics visualizations.
- Implement real Etsy API listing creation once credentials are approved.
- Expand logging and monitoring infrastructure.

## Git Workflow
- Use `git add .` / `git commit -m "<message>"` for changes.
- Keep feature work isolated and commit completed modules with clear messages.
- Push to remote `main` branch after local validation.

## Testing Commands
- Syntax check: `python -m py_compile <files>`.
- Run unit tests: `python -m unittest test_trend_score.py` (and future `test_trend_engine.py`, `test_upload_priority.py`).
- Validate CSV migrations by running product manager and import flows.

## Naming Conventions
- Packages under `ai_factory/` by domain.
- Modules named after capability: `analytics`, `intelligence`, `listings`, `maintenance`, `importers`, `tasks`.
- CSV-backed state uses descriptive names like `products.csv`, `task_queue.csv`, `workflow_history.csv`.

## Folder Structure
- `ai_factory/`: core packages and domain logic.
- `backups/`, `designs/`, `logs/`, `mockups/`, `snapshots/`, `visualizations/`: artifact directories.
- Root CSV files drive state and product inventory.

## Pending API Integrations
- Etsy API listing creation/update.
- External trend or marketplace data APIs.
- Potential future support for non-Etsy marketplaces.

## Known Bugs
- No known blocking syntax errors in current codebase.
- Trend and upload prioritization flows may need tuning for real data.
- Manual CSV migration paths should be validated on older files.

## Next Priorities
- Stabilize trend intelligence and upload prioritization in a marketplace-agnostic way.
- Add structured logging and monitoring.
- Build regression tests for the new trend engine and queue prioritization.
- Keep `AI_CONTEXT.md` updated with every major architecture or feature change.
