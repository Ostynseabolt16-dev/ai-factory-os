from __future__ import annotations

import html
import re
from datetime import datetime
from pathlib import Path

BASE_DIR = Path("/Users/ostynseabolt/ai/youtube")
AMBIENT_IDEAS_FILE = BASE_DIR / "ambient_ideas.txt"
FALLBACK_IDEAS_FILE = BASE_DIR / "ideas.txt"
IDEAS_FILE = AMBIENT_IDEAS_FILE if AMBIENT_IDEAS_FILE.exists() else FALLBACK_IDEAS_FILE
TITLES_DIR = BASE_DIR / "titles"
LOG_FILE = BASE_DIR / "production_log.txt"


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return slug[:80] or "ambient_video"


def read_ideas() -> list[str]:
    if not IDEAS_FILE.exists():
        raise FileNotFoundError(f"Missing ideas file: {IDEAS_FILE}")
    return [line.strip(" -\t\n") for line in IDEAS_FILE.read_text(encoding="utf-8").splitlines() if line.strip(" -\t\n")]


def existing_title_text() -> str:
    TITLES_DIR.mkdir(parents=True, exist_ok=True)
    return "\n".join(path.read_text(encoding="utf-8", errors="ignore").lower() for path in TITLES_DIR.glob("*.txt"))


def normalize_title(title: str) -> str:
    return re.sub(r"\s+", " ", title.strip().lower())


def pick_next_idea(ideas: list[str]) -> tuple[int, str, str]:
    existing = normalize_title(existing_title_text())
    already_made = {
        normalize_title("Cozy Coffee Shop Ambience | Rain Outside | 2 Hours"),
        normalize_title("Thunderstorm at Night | Deep Sleep Sounds | 2 Hours"),
    }
    for index, idea in enumerate(ideas, start=1):
        normalized = normalize_title(idea)
        if normalized not in already_made and normalized not in existing:
            return index, idea, "first idea not found in existing title files"
    raise RuntimeError("All ideas in ambient_ideas.txt appear to have been made already.")


def build_metadata(idea: str) -> dict[str, object]:
    clean = idea.strip()
    title = clean
    keyword = clean.lower()
    description = (
        f"Relax with {clean}, a calming ambient sound experience created for sleep, study, focus, meditation, and stress relief. "
        f"This 2 hour ambience video is designed for people who enjoy peaceful background audio, cozy environments, natural white noise, and relaxing soundscapes. "
        f"Use these ambient sounds while working, reading, journaling, resting, or winding down at night. "
        f"The steady atmosphere helps reduce distractions and creates a quiet space for concentration, deep relaxation, and better sleep. "
        f"If you enjoy rain sounds, cozy ambience, sleep sounds, study ambience, focus sounds, meditation ambience, relaxing background noise, white noise, and peaceful videos, this {keyword} video is made for you. "
        f"Play it in the background whenever you need a calm place to think, rest, focus, or reset your mind."
    )
    tags = [
        "ambient sounds", "sleep sounds", "study ambience", "focus sounds", "relaxing sounds",
        "white noise", "meditation sounds", "calm ambience", "background noise", "deep sleep",
        "stress relief", "cozy ambience", "peaceful sounds", "relaxation", keyword[:28],
    ]
    prompt = (
        f"Create a cozy photorealistic thumbnail scene for '{clean}', cinematic soft lighting, calm real-world setting, "
        "peaceful atmosphere, high detail, warm and relaxing mood, no text in the image"
    )
    if "library" in keyword:
        audio_search = "library rain ambience loop"
    elif "coffee" in keyword:
        audio_search = "coffee shop rain ambience"
    elif "thunderstorm" in keyword:
        audio_search = "thunderstorm night rain loop"
    elif "fireplace" in keyword:
        audio_search = "fireplace rain crackling loop"
    elif "forest" in keyword:
        audio_search = "forest morning rain birds"
    else:
        audio_search = "rain ambience loop"
    return {"title": title, "description": description, "tags": tags, "prompt": prompt, "audio_search": audio_search}


def save_metadata(video_number: int, metadata: dict[str, object]) -> Path:
    filename = f"{video_number:03d}_{slugify(str(metadata['title']))}.txt"
    path = TITLES_DIR / filename
    content = (
        f"TITLE:\n{metadata['title']}\n\n"
        f"DESCRIPTION:\n{metadata['description']}\n\n"
        f"TAGS:\n{', '.join(metadata['tags'])}\n\n"
        f"THUMBNAIL PROMPT:\n{metadata['prompt']}\n\n"
        f"AUDIO SEARCH TERM:\n{metadata['audio_search']}\n"
    )
    path.write_text(content, encoding="utf-8")
    return path


def save_upload_guide(video_number: int, metadata: dict[str, object]) -> Path:
    filename = f"{video_number:03d}_{slugify(str(metadata['title']))}_upload_guide.html"
    path = BASE_DIR / filename
    body = f"""
    <html><body>
    <h1>{html.escape(str(metadata['title']))}</h1>
    <h2>Description</h2><p>{html.escape(str(metadata['description']))}</p>
    <h2>Tags</h2><p>{html.escape(", ".join(metadata['tags']))}</p>
    <h2>Thumbnail Prompt</h2><p>{html.escape(str(metadata['prompt']))}</p>
    <h2>Freesound Search</h2><p>{html.escape(str(metadata['audio_search']))}</p>
    <h2>Render Command</h2>
    <code>./venv/bin/python youtube/make_video.py path/to/thumbnail.png path/to/audio.ogg</code>
    </body></html>
    """
    path.write_text(body, encoding="utf-8")
    return path


def log_video(title: str) -> None:
    timestamp = datetime.now().replace(microsecond=0).isoformat()
    with LOG_FILE.open("a", encoding="utf-8") as log:
        log.write(f"{timestamp} | {title} | metadata_ready\n")


def main() -> None:
    ideas = read_ideas()
    video_number, idea, reason = pick_next_idea(ideas)
    metadata = build_metadata(idea)
    metadata_path = save_metadata(video_number, metadata)
    guide_path = save_upload_guide(video_number, metadata)
    log_video(str(metadata["title"]))

    print(f"Picked idea #{video_number}: {idea}")
    print(f"Why: {reason}")
    print(f"\nTITLE:\n{metadata['title']}")
    print(f"\nDESCRIPTION:\n{metadata['description']}")
    print(f"\nTAGS:\n{', '.join(metadata['tags'])}")
    print(f"\nTHUMBNAIL PROMPT:\n{metadata['prompt']}")
    print(f"\nFREESOUND SEARCH TERM:\n{metadata['audio_search']}")
    print(f"\nSaved metadata: {metadata_path}")
    print(f"Saved upload guide: {guide_path}")
    print("\nRender reminder:")
    print("./venv/bin/python youtube/make_video.py path/to/thumbnail.png path/to/audio.ogg")


if __name__ == "__main__":
    main()
