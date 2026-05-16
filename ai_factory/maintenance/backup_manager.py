"""Local CSV backup snapshots."""

from __future__ import annotations

import shutil
from pathlib import Path

from ai_factory.config import PROJECT_ROOT
from ai_factory.tasks.task_models import now_iso

BACKUPS_DIR = PROJECT_ROOT / "backups"
BACKUP_FILES = ["products.csv", "task_queue.csv", "task_history.csv", "niche_report.csv"]


def _snapshot_name() -> str:
    return now_iso().replace(":", "-")


def create_backup_snapshot() -> Path:
    """Create a timestamped local snapshot of key CSV files."""
    base = BACKUPS_DIR / _snapshot_name()
    snapshot_dir = base
    counter = 2
    while snapshot_dir.exists():
        snapshot_dir = Path(f"{base}-{counter}")
        counter += 1
    snapshot_dir.mkdir(parents=True, exist_ok=False)
    for filename in BACKUP_FILES:
        source = PROJECT_ROOT / filename
        if source.exists():
            shutil.copy2(source, snapshot_dir / filename)
    return snapshot_dir


def list_backups() -> list[Path]:
    """List backup snapshot directories newest first."""
    if not BACKUPS_DIR.exists():
        return []
    return sorted([path for path in BACKUPS_DIR.iterdir() if path.is_dir()], reverse=True)


def restore_backup(backup_path: str | Path, *, confirm: bool = False) -> list[Path]:
    """
    Restore CSV files from a snapshot.

    Caller must pass confirm=True. This explicit flag prevents accidental
    overwrite from CLI or scripts.
    """
    if not confirm:
        raise ValueError("restore_backup requires confirm=True.")
    snapshot_dir = Path(backup_path)
    if not snapshot_dir.is_absolute():
        snapshot_dir = BACKUPS_DIR / snapshot_dir
    if not snapshot_dir.exists() or not snapshot_dir.is_dir():
        raise FileNotFoundError(f"Backup not found: {snapshot_dir}")

    restored: list[Path] = []
    for filename in BACKUP_FILES:
        source = snapshot_dir / filename
        if source.exists():
            target = PROJECT_ROOT / filename
            shutil.copy2(source, target)
            restored.append(target)
    return restored
