#!/usr/bin/env python3
"""Fix C6 variant-B: remove front license-plate pocket on collection master."""

from __future__ import annotations

import argparse
import shutil
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

DEFAULT_SRC = Path("designs/backups/c6_variant_B_collection_pre_plate_fix.png")
DEFAULT_OUT = Path("designs/corvette/c6_variant_B_collection.png")

# Legacy coords targeted the headlight — wrong. Real plate ~ (528, 622, 592, 638) @ 1536×1024.
PLATE_BOX_PCT = (0.332, 0.598, 0.398, 0.638)


@dataclass(frozen=True)
class PlateBox:
    x0: int
    y0: int
    x1: int
    y1: int

    @classmethod
    def from_pct(cls, w: int, h: int, pct: tuple[float, float, float, float]) -> PlateBox:
        x0, y0, x1, y1 = pct
        return cls(int(w * x0), int(h * y0), int(w * x1), int(h * y1))

    def pad(self, w: int, h: int, px: int = 4) -> PlateBox:
        return PlateBox(
            max(0, self.x0 - px),
            max(0, self.y0 - px),
            min(w, self.x1 + px),
            min(h, self.y1 + px),
        )


def _feather_mask(mask: np.ndarray, sigma: float) -> np.ndarray:
    return cv2.GaussianBlur(mask.astype(np.float32), (0, 0), sigma) / 255.0


def detect_plate_box(gray: np.ndarray) -> PlateBox | None:
    """Find the thin dark license-plate bar on the front bumper."""
    h, w = gray.shape
    best: tuple[float, int, int, int] | None = None
    for y in range(int(h * 0.58), int(h * 0.66)):
        row = gray[y, int(w * 0.32) : int(w * 0.42)]
        base = int(w * 0.32)
        for x in range(0, max(1, len(row) - 40)):
            for length in (45, 55, 65):
                if x + length >= len(row):
                    continue
                mean = float(row[x : x + length].mean())
                if mean > 40:
                    continue
                if best is None or mean < best[0]:
                    best = (mean, y, base + x, base + x + length)
    if best is None:
        return None
    _, y, x0, x1 = best
    return PlateBox(x0, y - 4, x1, y + 5).pad(w, h, 6)


def fix_plate_pocket(rgb: np.ndarray, box: PlateBox) -> np.ndarray:
    """Replace the plate pocket by blending bumper paint from left/right edges."""
    h, w = rgb.shape[:2]
    u8 = np.clip(rgb, 0, 255).astype(np.uint8)
    lum = u8.mean(axis=2)

    mask = np.zeros((h, w), np.uint8)
    cv2.rectangle(mask, (box.x0, box.y0), (box.x1, box.y1), 255, -1)

    donor = u8.copy()
    for y in range(box.y0, box.y1):
        left = u8[y, max(0, box.x0 - 16) : box.x0].mean(axis=0)
        right = u8[y, box.x1 : min(w, box.x1 + 16)].mean(axis=0)
        span = max(box.x1 - box.x0, 1)
        for x in range(box.x0, box.x1):
            t = (x - box.x0) / span
            donor[y, x] = np.clip((1 - t) * left + t * right, 0, 255)

    alpha = _feather_mask(mask, 2.8)[..., None]
    out = u8.astype(np.float32) * (1 - alpha) + donor.astype(np.float32) * alpha
    blended = np.clip(out, 0, 255).astype(np.uint8)

    speck = ((blended.mean(axis=2) < 32) & (mask > 0)).astype(np.uint8) * 255
    if speck.any():
        blended = cv2.inpaint(blended, speck, 2, cv2.INPAINT_TELEA)

    return blended.astype(np.float32)


def fix_c6_master(rgba: np.ndarray, box: PlateBox | None = None) -> np.ndarray:
    rgb = rgba[:, :, :3].astype(np.float32)
    h, w = rgb.shape[:2]
    plate = box or detect_plate_box(rgb.mean(axis=2)) or PlateBox.from_pct(w, h, PLATE_BOX_PCT)
    rgb = fix_plate_pocket(rgb, plate.pad(w, h, 2))
    out = rgba.copy()
    out[:, :, :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--src", type=Path, default=DEFAULT_SRC)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--backup-out", action="store_true")
    parser.add_argument("--debug-crop", type=Path, default=None, help="Write plate QC crop here")
    args = parser.parse_args()

    img = np.array(Image.open(args.src).convert("RGBA"))
    gray = img[:, :, :3].mean(axis=2)
    h, w = gray.shape
    box = detect_plate_box(gray) or PlateBox.from_pct(w, h, PLATE_BOX_PCT)
    fixed = fix_c6_master(img, box)

    if args.backup_out and args.out.exists():
        shutil.copy2(args.out, args.out.with_name(args.out.stem + "_pre_plate_fix.png"))

    Image.fromarray(fixed, "RGBA").save(args.out)
    print(f"OK  {args.out}  plate_box=({box.x0},{box.y0})-({box.x1},{box.y1})")

    debug = args.debug_crop or Path("designs/_qc_plate_after_fix.png")
    crop = fixed[
        max(0, box.y0 - 30) : min(h, box.y1 + 30),
        max(0, box.x0 - 40) : min(w, box.x1 + 40),
    ]
    Image.fromarray(crop, "RGBA").save(debug)
    print(f"QC  {debug}")


if __name__ == "__main__":
    main()
