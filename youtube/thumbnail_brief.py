from __future__ import annotations

import re
from hashlib import md5
from pathlib import Path

BASE_DIR = Path("/Users/ostynseabolt/ai/youtube")
THUMBNAILS_DIR = BASE_DIR / "thumbnails"

PALETTES = [
    ("#0A192F", "#00D8FF", "#FF4E50"),
    ("#1F2022", "#FFD166", "#EF476F"),
    ("#081C15", "#7BE495", "#F9DC5C"),
    ("#2D1537", "#F08A5D", "#B83B5E"),
    ("#0B132B", "#5BC0EB", "#4D908E"),
    ("#1B262C", "#BBE1FA", "#0F4C75"),
]
EMOTIONS = [
    "shocked curiosity",
    "confident excitement",
    "bold challenge",
    "determined focus",
    "amazed surprise",
    "urgent curiosity",
]


def _safe_filename(title: str) -> str:
    text = title.strip().lower()
    text = re.sub(r"[^a-z0-9 _-]", "", text)
    text = re.sub(r"\s+", "_", text)
    return (text or "thumbnail")[:100]


def _choose_palette(title: str) -> tuple[str, str, str]:
    index = int(md5(title.encode("utf-8")).hexdigest(), 16) % len(PALETTES)
    return PALETTES[index]


def _choose_background_color(palette: tuple[str, str, str]) -> str:
    return palette[0]


def _choose_main_text(title: str) -> str:
    words = re.findall(r"[A-Za-z0-9]+", title)
    if not words:
        return "AI Business"
    priority = [word for word in words if len(word) > 3]
    if len(priority) >= 4:
        selected = priority[:4]
    else:
        selected = words[:4]
    return " ".join(selected).title()


def _choose_emotion(title: str) -> str:
    index = int(md5((title + "emotion").encode("utf-8")).hexdigest(), 16) % len(EMOTIONS)
    return EMOTIONS[index]


def generate_thumbnail_brief(title: str) -> str:
    THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)

    palette = _choose_palette(title)
    background_color = _choose_background_color(palette)
    main_text = _choose_main_text(title)
    emotion = _choose_emotion(title)
    color_scheme = palette
    style = "bold, high contrast, curiosity-gap"

    brief = [
        f"Title: {title}",
        f"Background color recommendation: {background_color}",
        f"Main text (max 4 words): {main_text}",
        f"Emotion/face expression to use: {emotion}",
        f"Color scheme (3 hex codes): {', '.join(color_scheme)}",
        f"Style: {style}",
        "",
        "Exact prompt for ChatGPT or Midjourney:",
        "-----------------------------------",
    ]

    prompt = (
        f"Create a bold YouTube thumbnail for a faceless AI business video titled \"{title}\". "
        f"Use a strong background color of {background_color} and a three-color palette of {', '.join(color_scheme)}. "
        f"Display the headline text '{main_text}' in large, high-contrast letters. "
        f"Use a striking curiosity-gap layout with {emotion} expression, simple AI or business iconography, and clean modern type. "
        "Keep the look bold, dramatic, and easy to read on mobile."
    )

    brief.append(prompt)
    brief_text = "\n".join(brief) + "\n"

    output_name = _safe_filename(title) + ".txt"
    output_path = THUMBNAILS_DIR / output_name
    output_path.write_text(brief_text, encoding="utf-8")

    print(brief_text)
    return str(output_path)


if __name__ == "__main__":
    import sys

    if len(sys.argv) <= 1:
        print("Usage: python thumbnail_brief.py \"My video title\"")
        raise SystemExit(1)

    video_title = " ".join(sys.argv[1:]).strip()
    path = generate_thumbnail_brief(video_title)
    print(f"Thumbnail brief saved to: {path}")
