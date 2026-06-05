#!/usr/bin/env python3
"""Recover streetwear PNGs from Cursor assets → designs/ → Printify-ready."""

from __future__ import annotations

import shutil
import subprocess
import sys
from collections import deque
from pathlib import Path

from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ASSETS = Path.home() / ".cursor/projects/Users-ostynseabolt-ai/assets"
DESIGNS = PROJECT_ROOT / "designs"
PREPARE = PROJECT_ROOT / "scripts/prepare_printify.py"
KNOCKOUT = PROJECT_ROOT / "scripts/knockout_connected_black_background.py"
# (source in assets, dest stem, color_mode)
# color_mode: mono = solid black POD export, color = keep car color, back = typographic back
RECOVER: list[tuple[str, str, str]] = [
    ("corvette_c5_streetwear_design.png", "corvette_c5_streetwear_design", "mono"),
    ("corvette_c5_yellow_streetwear_design.png", "corvette_c5_yellow_streetwear_design", "color"),
    ("corvette_c6_streetwear_design.png", "corvette_c6_streetwear_design", "mono"),
    ("corvette_c7_streetwear_design.png", "corvette_c7_streetwear_design", "mono"),
    ("corvette_c8_streetwear_design.png", "corvette_c8_streetwear_design", "mono"),
    ("corvette_c8_streetwear_back_design.png", "corvette_c8_streetwear_back_design", "back"),
    ("mustang_gt_streetwear_design.png", "mustang_gt_streetwear_design", "mono"),
    ("supra_mk4_streetwear_design.png", "supra_mk4_streetwear_design", "mono"),
    ("challenger_srt_streetwear_design.png", "challenger_srt_streetwear_design", "mono"),
    ("cab4dbf7-ea2d-46da-9dbb-b605a939a449.png", "skyline_r34_streetwear_design", "mono"),
]


def _corner_rgb(path: Path) -> tuple[int, int, int]:
    im = Image.open(path).convert("RGB")
    w, h = im.size
    px = im.load()
    samples = [px[0, 0], px[w - 1, 0], px[0, h - 1], px[w - 1, h - 1]]
    return tuple(sum(c[i] for c in samples) // 4 for i in range(3))


def _remove_light_bg(path: Path) -> None:
    """Flood-fill edge-connected near-white / checkerboard pixels to transparent."""
    im = Image.open(path).convert("RGBA")
    px = im.load()
    w, h = im.size

    def is_bg(r: int, g: int, b: int) -> bool:
        avg = (r + g + b) / 3
        spread = max(r, g, b) - min(r, g, b)
        return avg > 175 and spread < 25

    visited: set[tuple[int, int]] = set()
    q: deque[tuple[int, int]] = deque()
    for x in range(w):
        q.append((x, 0))
        q.append((x, h - 1))
    for y in range(h):
        q.append((0, y))
        q.append((w - 1, y))

    while q:
        x, y = q.popleft()
        if (x, y) in visited or x < 0 or y < 0 or x >= w or y >= h:
            continue
        r, g, b, _ = px[x, y]
        if not is_bg(r, g, b):
            continue
        visited.add((x, y))
        px[x, y] = (r, g, b, 0)
        q.extend([(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)])

    im.save(path)


def _process_transparency(path: Path, mode: str) -> str:
    r, g, b = _corner_rgb(path)
    avg = (r + g + b) / 3

    if avg > 128:
        _remove_light_bg(path)
        return "checkerboard/light bg removed"

    subprocess.run([sys.executable, str(KNOCKOUT), str(path)], check=True)
    return "black edge knockout"


def _prepare_printify(src: Path, dest: Path) -> None:
    subprocess.run(
        [sys.executable, str(PREPARE), str(src), "-o", str(dest)],
        check=True,
    )


def main() -> int:
    if not ASSETS.exists():
        print(f"Assets folder not found: {ASSETS}", file=sys.stderr)
        return 1

    DESIGNS.mkdir(parents=True, exist_ok=True)
    results: list[str] = []

    for src_name, stem, mode in RECOVER:
        src = ASSETS / src_name
        if not src.exists():
            print(f"SKIP missing: {src_name}")
            continue

        dest = DESIGNS / f"{stem}.png"
        shutil.copy2(src, dest)
        step = _process_transparency(dest, mode)

        fix_script = PROJECT_ROOT / "scripts/fix_letter_interior_white.py"
        subprocess.run(
            [sys.executable, str(fix_script), "--no-restore", stem],
            check=True,
        )

        printify_out = DESIGNS / f"{stem}_UPLOAD_TO_PRINTIFY.png"
        results.append(f"  {stem}.png + {printify_out.name} ({step} + letter fix)")

    print("\nRecovered:")
    print("\n".join(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
