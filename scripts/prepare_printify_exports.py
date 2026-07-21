#!/usr/bin/env python3
"""Prepare streetwear designs for Printify: knock out white, trim, size to DTG canvas."""

from __future__ import annotations

import argparse
from collections import deque
from pathlib import Path

from PIL import Image

# Matches existing corvette *_UPLOAD_TO_PRINTIFY.png exports in designs/
PRINTIFY_CANVAS = (3951, 4919)
TARGET_CONTENT_WIDTH = 2470  # same visual scale as corvette_c5_streetwear_design_UPLOAD_TO_PRINTIFY.png


def _is_background_pixel(r: int, g: int, b: int, a: int, threshold: int) -> bool:
    if a == 0:
        return True
    return r >= threshold and g >= threshold and b >= threshold


def remove_white_background(image: Image.Image, threshold: int = 242) -> Image.Image:
    """Flood-fill white from image edges so interior whites (distress specks) stay."""
    img = image.convert("RGBA")
    width, height = img.size
    pixels = img.load()
    visited: set[tuple[int, int]] = set()
    queue: deque[tuple[int, int]] = deque()

    for x in range(width):
        queue.append((x, 0))
        queue.append((x, height - 1))
    for y in range(height):
        queue.append((0, y))
        queue.append((width - 1, y))

    while queue:
        x, y = queue.popleft()
        if (x, y) in visited or x < 0 or y < 0 or x >= width or y >= height:
            continue
        r, g, b, a = pixels[x, y]
        if not _is_background_pixel(r, g, b, a, threshold):
            continue
        visited.add((x, y))
        pixels[x, y] = (r, g, b, 0)
        queue.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))

    return img


def _ring_luminance(
    pixels,
    component: list[tuple[int, int]],
    *,
    width: int,
    height: int,
    radius: int,
) -> float:
    """Average luminance of opaque pixels bordering a white component."""
    comp_set = set(component)
    lums: list[float] = []
    for cx, cy in component:
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if dx * dx + dy * dy > radius * radius:
                    continue
                x, y = cx + dx, cy + dy
                if (x, y) in comp_set or x < 0 or y < 0 or x >= width or y >= height:
                    continue
                r, g, b, a = pixels[x, y]
                if a == 0:
                    continue
                lums.append((r + g + b) / 3)
    return sum(lums) / len(lums) if lums else 255.0


def remove_enclosed_white(
    image: Image.Image,
    *,
    threshold: int = 242,
    ring_lum_max: float = 170.0,
    ring_radius: int = 3,
    content_bbox: tuple[int, int, int, int] | None = None,
    y_fraction_min: float | None = None,
    y_fraction_max: float | None = None,
) -> Image.Image:
    """Knock out white trapped inside letter counters and logo holes.

    Edge-connected background white must already be removed. Remaining white blobs
    surrounded by dark ink (low ring luminance) become transparent so the design
    prints correctly on dark shirts. Bright car highlights stay (high ring luminance).

    Optional y-fraction limits restrict knock-out to part of the artwork (used after
    upscale so headlights in the middle band are preserved).
    """
    img = image.convert("RGBA")
    width, height = img.size
    pixels = img.load()
    seen: set[tuple[int, int]] = set()
    bbox_top = content_bbox[1] if content_bbox else 0
    bbox_bottom = content_bbox[3] if content_bbox else height
    bbox_height = max(bbox_bottom - bbox_top, 1)

    for y in range(height):
        for x in range(width):
            if (x, y) in seen:
                continue
            r, g, b, a = pixels[x, y]
            if a == 0 or not _is_background_pixel(r, g, b, a, threshold):
                continue

            component: list[tuple[int, int]] = []
            queue: deque[tuple[int, int]] = deque([(x, y)])
            seen.add((x, y))
            while queue:
                cx, cy = queue.popleft()
                component.append((cx, cy))
                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if (nx, ny) in seen or nx < 0 or ny < 0 or nx >= width or ny >= height:
                        continue
                    nr, ng, nb, na = pixels[nx, ny]
                    if na == 0 or not _is_background_pixel(nr, ng, nb, na, threshold):
                        continue
                    seen.add((nx, ny))
                    queue.append((nx, ny))

            center_y = sum(cy for _, cy in component) / len(component)
            if y_fraction_min is not None or y_fraction_max is not None:
                y_frac = (center_y - bbox_top) / bbox_height
                if y_fraction_min is not None and y_frac < y_fraction_min:
                    continue
                if y_fraction_max is not None and y_frac > y_fraction_max:
                    continue

            ring_lum = _ring_luminance(
                pixels,
                component,
                width=width,
                height=height,
                radius=ring_radius,
            )
            if ring_lum <= ring_lum_max:
                for cx, cy in component:
                    cr, cg, cb, _ = pixels[cx, cy]
                    pixels[cx, cy] = (cr, cg, cb, 0)

    return img


def remove_enclosed_white_after_upscale(image: Image.Image, *, threshold: int = 242) -> Image.Image:
    """Re-clean counters after LANCZOS upscale without touching headlight glow."""
    bbox = image.getchannel("A").getbbox()
    if bbox is None:
        return image

    # Bottom band: V8 + paragraph counters (resize often pushes ring luminance upward).
    image = remove_enclosed_white(
        image,
        threshold=threshold,
        ring_lum_max=240.0,
        content_bbox=bbox,
        y_fraction_min=0.62,
    )
    # Top band: large generation badge holes (e.g. inside the C6 "6").
    image = remove_enclosed_white(
        image,
        threshold=threshold,
        ring_lum_max=240.0,
        content_bbox=bbox,
        y_fraction_max=0.40,
    )
    return image


def trim_transparent(image: Image.Image, padding: int = 0) -> Image.Image:
    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    if not bbox:
        raise ValueError("Image has no visible content after background removal.")
    left, top, right, bottom = bbox
    left = max(0, left - padding)
    top = max(0, top - padding)
    right = min(image.width, right + padding)
    bottom = min(image.height, bottom + padding)
    return image.crop((left, top, right, bottom))


def fit_on_printify_canvas(image: Image.Image, target_width: int = TARGET_CONTENT_WIDTH) -> Image.Image:
    scale = target_width / image.width
    new_size = (max(1, int(round(image.width * scale))), max(1, int(round(image.height * scale))))
    resized = image.resize(new_size, Image.Resampling.LANCZOS)

    canvas = Image.new("RGBA", PRINTIFY_CANVAS, (0, 0, 0, 0))
    x = (PRINTIFY_CANVAS[0] - resized.width) // 2
    y = (PRINTIFY_CANVAS[1] - resized.height) // 2
    canvas.alpha_composite(resized, (x, y))
    return canvas


def prepare_printify_export(
    input_path: Path,
    output_path: Path | None = None,
    *,
    threshold: int = 242,
    knock_out_counters: bool = True,
    ring_lum_max: float = 170.0,
) -> Path:
    if output_path is None:
        output_path = input_path.with_name(f"{input_path.stem}_UPLOAD_TO_PRINTIFY.png")

    image = Image.open(input_path).convert("RGBA")
    image = remove_white_background(image, threshold=threshold)
    if knock_out_counters:
        image = remove_enclosed_white(image, threshold=threshold, ring_lum_max=ring_lum_max)
    image = trim_transparent(image, padding=8)
    image = fit_on_printify_canvas(image)
    if knock_out_counters:
        image = remove_enclosed_white_after_upscale(image, threshold=threshold)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, format="PNG", optimize=True)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare PNG designs for Printify DTG upload.")
    parser.add_argument(
        "inputs",
        nargs="*",
        type=Path,
        help="Design PNG paths (default: C5-C8 safe variant B collection)",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=242,
        help="White background cutoff (0-255). Lower = more aggressive knock-out.",
    )
    parser.add_argument(
        "--no-knock-out-counters",
        action="store_true",
        help="Skip removing white trapped inside letter counters (8, C5/C6, paragraph).",
    )
    parser.add_argument(
        "--ring-lum-max",
        type=float,
        default=170.0,
        help="Max average border luminance for enclosed white knock-out (0-255).",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    default_inputs = [
        repo_root / "designs/corvette/c5_variant_B_blackwheels_plate.png",
        repo_root / "designs/corvette/c6_variant_B_collection.png",
        repo_root / "designs/corvette/c7_variant_B_collection.png",
        repo_root / "designs/corvette/c8_variant_B_collection.png",
    ]
    inputs = args.inputs or default_inputs

    for input_path in inputs:
        resolved = input_path if input_path.is_absolute() else repo_root / input_path
        if not resolved.exists():
            raise FileNotFoundError(f"Design not found: {resolved}")
        output = prepare_printify_export(
            resolved,
            threshold=args.threshold,
            knock_out_counters=not args.no_knock_out_counters,
            ring_lum_max=args.ring_lum_max,
        )
        with Image.open(output) as saved:
            alpha = saved.getchannel("A").getextrema()
        print(f"OK  {output.name}  {saved.size}  alpha={alpha}")


if __name__ == "__main__":
    main()
