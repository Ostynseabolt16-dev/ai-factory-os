"""Paths and environment for the whole project."""

from pathlib import Path

from dotenv import load_dotenv

# Project root = parent of the `ai_factory` package (works regardless of cwd if imported from repo).
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load .env from project root once when this module is imported.
load_dotenv(PROJECT_ROOT / ".env")

# Generated PNGs (legacy path — keep stable so existing workflows keep working).
DESIGNS_DIR = PROJECT_ROOT / "designs"

# Generated listing mockups.
MOCKUPS_DIR = PROJECT_ROOT / "mockups"

# Product registry (CSV until you add a database).
PRODUCTS_CSV = PROJECT_ROOT / "products.csv"

# Persistent task orchestration files.
TASK_QUEUE_CSV = PROJECT_ROOT / "task_queue.csv"
TASK_HISTORY_CSV = PROJECT_ROOT / "task_history.csv"

# Explicit workflow scheduling history.
WORKFLOW_HISTORY_CSV = PROJECT_ROOT / "workflow_history.csv"
