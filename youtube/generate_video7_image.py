#!/usr/bin/env python3
"""One-off: generate video 7 still (rainy window + bookshelf)."""

from pathlib import Path

from ai_factory.generation.openai_image import generate_simple_image_to_file

PROMPT = """
Photorealistic close-up of a rain-soaked window at night, water droplets sharply in focus on the glass,
blurred warm bookshelf and books in the background, moody cool-warm color grading,
soft amber desk lamp light indoors contrasting with cool gray rainy darkness outside,
cozy intimate sleep-friendly atmosphere, cinematic shallow depth of field,
no people, no text, no watermark, no logo, landscape composition
""".strip()

OUT = Path(__file__).resolve().parents[1] / "designs" / "rainy_window_library_books.png"


def main() -> None:
    path = generate_simple_image_to_file(
        PROMPT,
        OUT,
        size="1536x1024",
    )
    print(path)


if __name__ == "__main__":
    main()
