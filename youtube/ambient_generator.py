from pathlib import Path

BASE_DIR = Path("/Users/ostynseabolt/ai/youtube/titles")

VIDEOS = [
    {
        "title": "3 Hours of Heavy Rain on a Cabin Roof | Sleep & Study",
        "setting": "heavy rain on a quiet cabin roof",
        "use": "sleep, studying, relaxation, and deep focus",
        "prompt": "A cozy photorealistic wooden cabin in a forest at night, heavy rain falling on the roof, warm window light, misty trees, peaceful atmosphere, no text in image",
        "tags": ["rain sounds", "cabin rain", "sleep sounds", "study ambience", "heavy rain", "relaxing rain", "deep sleep", "focus sounds", "cozy cabin", "night rain"],
    },
    {
        "title": "Cozy Coffee Shop Ambience | Rain Outside | 2 Hours",
        "setting": "a warm coffee shop while rain falls outside",
        "use": "focus, reading, studying, and calm background noise",
        "prompt": "A cozy photorealistic coffee shop interior on a rainy day, warm lights, wooden tables, rain on windows, soft cozy atmosphere, no text in image",
        "tags": ["coffee ambience", "rain outside", "study sounds", "cozy cafe", "focus music", "reading sounds", "rain ambience", "cafe sounds", "work ambience", "calm rain"],
    },
    {
        "title": "Thunderstorm at Night | Deep Sleep Sounds | 3 Hours",
        "setting": "a nighttime thunderstorm with steady rain",
        "use": "deep sleep, relaxation, stress relief, and nighttime rest",
        "prompt": "A photorealistic quiet bedroom at night during a thunderstorm, rain on the window, soft blankets, dim lamp glow, peaceful mood, no text in image",
        "tags": ["thunderstorm", "sleep sounds", "night rain", "deep sleep", "rain thunder", "storm sounds", "relaxing storm", "sleep ambience", "dark rain", "calm thunder"],
    },
    {
        "title": "Quiet Library Ambience | Soft Rain | Focus & Study",
        "setting": "a quiet library with soft rain outside",
        "use": "focused studying, reading, writing, and productivity",
        "prompt": "A photorealistic quiet library with tall shelves, warm desk lamps, soft rain on large windows, cozy study atmosphere, no text in image",
        "tags": ["library ambience", "soft rain", "study ambience", "focus sounds", "reading sounds", "quiet library", "rain study", "productivity", "calm ambience", "study rain"],
    },
    {
        "title": "Rainy Day at Home | Fireplace Crackling | 2 Hours",
        "setting": "a rainy day at home with a crackling fireplace",
        "use": "cozy relaxation, reading, resting, and peaceful background sound",
        "prompt": "A cozy photorealistic living room on a rainy day, fireplace crackling, warm blankets, rain on windows, soft natural light, no text in image",
        "tags": ["fireplace sounds", "rainy day", "home ambience", "cozy rain", "relaxing sounds", "reading ambience", "fire crackling", "calm home", "rain sounds", "cozy fireplace"],
    },
]


def write_video_file(index, video):
    description = (
        f"Enjoy {video['title']} with a calming real-world atmosphere. "
        f"This ambient video features {video['setting']} for {video['use']}. "
        "Use it as background sound for sleep, study, work, reading, or relaxation. "
        "The natural rain and cozy ambience help create a peaceful environment with fewer distractions. "
        "Play this video whenever you need relaxing ambient sounds and a calm place to focus."
    )
    content = (
        f"Final YouTube title:\n{video['title']}\n\n"
        f"Description:\n{description}\n\n"
        f"Tags:\n{', '.join(video['tags'])}\n\n"
        f"Thumbnail image prompt:\n{video['prompt']}\n"
    )
    filename = f"ambient_video_{index}.txt"
    (BASE_DIR / filename).write_text(content, encoding="utf-8")


def main():
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    for index, video in enumerate(VIDEOS, start=1):
        write_video_file(index, video)
    print("Done - 5 ambient videos ready")


if __name__ == "__main__":
    main()
