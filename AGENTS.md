# AGENTS.md

> Business context, priorities, and hard rules for this shop live in `.cursor/rules/cozy-orbit-agent.mdc`,
> `README.md`, `AI_CONTEXT.md`, and `designs/listings/SHOP_STATE.md`. Read those for what to work on.
> This file only covers how to run/test/develop the code.

## Cursor Cloud specific instructions

This repo is a **local-first Python CLI** (`ai-factory-os` / CozyOrbitPrints ops tooling) with
CSV-backed state. There is **no server, database, or web service to start** — everything runs as
one-off Python commands. Python 3.12 is used.

### Environment
- Dependencies live in a virtualenv at `.venv/` (system Python is PEP-668 "externally managed", so a
  venv is required — do not `pip install` into system Python). The startup update script recreates/refreshes
  `.venv` from `requirements.txt`, so on a fresh agent the venv already exists.
- Run everything with `.venv/bin/python ...` (the repo's docs and the `.cursor` rule assume this).

### Lint / test / build / run
- Tests (fast, no network): `.venv/bin/python -m unittest discover -s . -p "test_*.py"`
- Syntax / "lint" check: `.venv/bin/python -m compileall ai_factory` (there is no ruff/flake8/pylint config).
- Daily ops brief (safe, read-only, documented session-start command):
  `.venv/bin/python scripts/shop_daily_brief.py`
- Interactive CLI (numbered menu, feed input on stdin when headless):
  `.venv/bin/python -m ai_factory.cli`
- More commands are listed in `dev_commands.md`.

### Non-obvious gotchas
- **Some CLI options rewrite tracked files as a side effect.** Running the founder dashboard
  (option `1`) and rebuilding the dashboard (options `77`/`91`/`92`) regenerate/normalize files such as
  `products.csv`, `duplicate_report.csv`, and `visualizations/homebase_factory_map.html` (fresh
  timestamps, recomputed `age_days`, sanitized rows). If you only ran them to inspect output, run
  `git checkout -- <file>` afterward so you don't commit unintended data churn.
- **Options `77`/`92` try to open a browser** (`webbrowser`/`xdg-open`). Prefer option `91`
  ("Rebuild Etsy sync dashboard") when headless — it regenerates the same HTML without opening a browser.
- **OpenAI-dependent commands cost money and need `OPENAI_API_KEY`.** `main.py` (batch pipeline) and
  `scripts/generate_*.py` call OpenAI image/text generation. Per the shop rules, do **not** run them
  without explicit owner approval. Everything else (analytics, scoring, reports, exports, dashboard,
  tests) runs fully offline against the CSVs.
- **There is no Etsy API integration** — all listing/upload work is manual browser + paste from
  `designs/listings/*.md`. CLI "upload" options operate on local queues/export packages only.
