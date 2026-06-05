#!/usr/bin/env python3
"""
Remove white/checkerboard fills inside letters, captions, and car windows for POD.

Touches header, model badge, description paragraph, and car glass zones.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from collections import deque
from pathlib import Path

from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DESIGNS = PROJECT_ROOT / "designs"
ASSETS = Path.home() / ".cursor/projects/Users-ostynseabolt-ai/assets"
PREPARE = PROJECT_ROOT / "scripts/prepare_printify.py"

STREETWEAR_STEMS = [
    "corvette_c5_streetwear_design",
    "corvette_c5_yellow_streetwear_design",
    "corvette_c6_streetwear_design",
    "corvette_c7_streetwear_design",
    "corvette_c8_streetwear_design",
    "corvette_c8_streetwear_back_design",
    "mustang_gt_streetwear_design",
    "supra_mk4_streetwear_design",
    "challenger_srt_streetwear_design",
    "skyline_r34_streetwear_design",
]

ASSET_MAP = {
    "corvette_c5_streetwear_design": "corvette_c5_streetwear_design.png",
    "corvette_c5_yellow_streetwear_design": "corvette_c5_yellow_streetwear_design.png",
    "corvette_c6_streetwear_design": "corvette_c6_streetwear_design.png",
    "corvette_c7_streetwear_design": "corvette_c7_streetwear_design.png",
    "corvette_c8_streetwear_design": "corvette_c8_streetwear_design.png",
    "corvette_c8_streetwear_back_design": "corvette_c8_streetwear_back_design.png",
    "mustang_gt_streetwear_design": "mustang_gt_streetwear_design.png",
    "supra_mk4_streetwear_design": "supra_mk4_streetwear_design.png",
    "challenger_srt_streetwear_design": "challenger_srt_streetwear_design.png",
    "skyline_r34_streetwear_design": "cab4dbf7-ea2d-46da-9dbb-b605a939a449.png",
}


def remove_light_edge(path: Path) -> None:
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
        q.extend([(x, 0), (x, h - 1)])
    for y in range(h):
        q.extend([(0, y), (w - 1, y)])

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


def _is_yellow(r: int, g: int, b: int) -> bool:
    return r > 150 and g > 120 and b < 130 and r >= g


def _is_letter_fill(r: int, g: int, b: int) -> bool:
    avg = (r + g + b) / 3
    spread = max(r, g, b) - min(r, g, b)
    return avg >= 165 and spread < 35


def _is_dark(r: int, g: int, b: int) -> bool:
    return (r + g + b) / 3 <= 110


def _touches_dark_opaque(px, x: int, y: int, w: int, h: int) -> bool:
    for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
        if nx < 0 or ny < 0 or nx >= w or ny >= h:
            continue
        rr, gg, bb, aa = px[nx, ny]
        if aa > 0 and _is_dark(rr, gg, bb):
            return True
    return False


def _in_fix_zone(x: int, y: int, w: int, h: int, *, back_only: bool) -> bool:
    if back_only:
        return True
    header = y < int(h * 0.42)
    badge = y > int(h * 0.58) and x < int(w * 0.45)
    caption = y > int(h * 0.70) and x > int(w * 0.30)
    car = int(h * 0.30) < y < int(h * 0.80) and int(w * 0.05) < x < int(w * 0.95)
    return header or badge or caption or car


def _in_caption_zone(x: int, y: int, w: int, h: int) -> bool:
    return y > int(h * 0.70) and x > int(w * 0.30)


def _in_car_zone(x: int, y: int, w: int, h: int) -> bool:
    return int(h * 0.30) < y < int(h * 0.80) and int(w * 0.05) < x < int(w * 0.95)


def _in_windshield_zone(x: int, y: int, w: int, h: int) -> bool:
    return int(h * 0.32) < y < int(h * 0.58) and int(w * 0.28) < x < int(w * 0.82)


def _is_car_glass_fill(r: int, g: int, b: int) -> bool:
    avg = (r + g + b) / 3
    spread = max(r, g, b) - min(r, g, b)
    return avg >= 155 and spread < 40


def _dark_neighbors8(px, x: int, y: int, w: int, h: int, *, threshold: int = 130) -> int:
    count = 0
    for nx in range(max(0, x - 1), min(w, x + 2)):
        for ny in range(max(0, y - 1), min(h, y + 2)):
            if nx == x and ny == y:
                continue
            rr, gg, bb, aa = px[nx, ny]
            if aa > 0 and (rr + gg + bb) / 3 <= threshold:
                count += 1
    return count


def fix_letter_interior(
    path: Path,
    *,
    color_car: bool = False,
    back_only: bool = False,
) -> int:
    im = Image.open(path).convert("RGBA")
    px = im.load()
    w, h = im.size
    removed = 0

    for y in range(h):
        for x in range(w):
            if not _in_fix_zone(x, y, w, h, back_only=back_only):
                continue
            r, g, b, a = px[x, y]
            if a == 0 or not _is_letter_fill(r, g, b):
                continue
            if color_car and _is_yellow(r, g, b):
                continue
            if _touches_dark_opaque(px, x, y, w, h):
                px[x, y] = (r, g, b, 0)
                removed += 1

    im.save(path)
    return removed


def fix_caption_and_car_glass(
    path: Path,
    *,
    color_car: bool = False,
    back_only: bool = False,
) -> int:
    im = Image.open(path).convert("RGBA")
    px = im.load()
    w, h = im.size
    removed = 0

    if not back_only:
        # Caption: remove bright white/checkerboard inside letter counters and haze box.
        for y in range(h):
            for x in range(w):
                if not _in_caption_zone(x, y, w, h):
                    continue
                r, g, b, a = px[x, y]
                if a == 0:
                    continue
                avg = (r + g + b) / 3
                spread = max(r, g, b) - min(r, g, b)
                if avg >= 175 and spread < 40:
                    px[x, y] = (r, g, b, 0)
                    removed += 1

        # Windshield / cabin: clear large light fills (common Supra/Challenger artifact).
        for y in range(h):
            for x in range(w):
                if not _in_windshield_zone(x, y, w, h):
                    continue
                r, g, b, a = px[x, y]
                if a == 0:
                    continue
                if color_car and _is_yellow(r, g, b):
                    continue
                avg = (r + g + b) / 3
                spread = max(r, g, b) - min(r, g, b)
                if avg >= 120 and spread < 55:
                    px[x, y] = (r, g, b, 0)
                    removed += 1

        # Car glass / window whites and leftover checkerboard elsewhere on body.
        for _ in range(3):
            for y in range(h):
                for x in range(w):
                    if not _in_car_zone(x, y, w, h) or _in_windshield_zone(x, y, w, h):
                        continue
                    r, g, b, a = px[x, y]
                    if a == 0 or not _is_car_glass_fill(r, g, b):
                        continue
                    if color_car and _is_yellow(r, g, b):
                        continue
                    if _dark_neighbors8(px, x, y, w, h, threshold=155) >= 1:
                        px[x, y] = (r, g, b, 0)
                        removed += 1

    im.save(path)
    return removed


def process_file(path: Path, *, color_car: bool = False, back_only: bool = False) -> int:
    n1 = fix_letter_interior(path, color_car=color_car, back_only=back_only)
    n2 = fix_caption_and_car_glass(path, color_car=color_car, back_only=back_only)
    return n1 + n2


def restore_from_assets(stem: str) -> Path:
    import shutil

    src = ASSETS / ASSET_MAP[stem]
    dest = DESIGNS / f"{stem}.png"
    shutil.copy2(src, dest)
    remove_light_edge(dest)
    return dest


def prepare_printify(src: Path) -> Path:
    dest = src.with_name(f"{src.stem}_UPLOAD_TO_PRINTIFY.png")
    subprocess.run([sys.executable, str(PREPARE), str(src), "-o", str(dest)], check=True)
    return dest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-restore", action="store_true", help="Fix in place; do not copy from assets")
    parser.add_argument("stems", nargs="*", help="Design stems (default: full batch)")
    args = parser.parse_args()
    stems = args.stems or STREETWEAR_STEMS

    for stem in stems:
        path = DESIGNS / f"{stem}.png"
        if not args.no_restore:
            if stem not in ASSET_MAP:
                print(f"SKIP unknown stem: {stem}")
                continue
            path = restore_from_assets(stem)
        elif not path.exists():
            print(f"SKIP missing: {path}")
            continue
        else:
            remove_light_edge(path)

        color_car = "yellow" in stem
        back_only = "back" in stem
        n = process_file(path, color_car=color_car, back_only=back_only)
        out = prepare_printify(path)
        print(f"{stem}: removed {n} -> {out.name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
