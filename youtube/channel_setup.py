from __future__ import annotations

from pathlib import Path


BASE_DIR = Path("/Users/ostynseabolt/ai/youtube")
SUBDIRS = ["scripts", "titles", "thumbnails", "uploaded"]
IDEAS = [
    "I built an AI Etsy shop in 24 hours with no coding experience",
    "Day 3: My AI factory made its first sale",
    "5 AI tools that actually make money in 2025",
    "I let AI run my business for a week",
    "How I automated my Etsy shop with Python",
    "My AI side hustle income report: week 1",
    "The $100 AI business challenge",
    "I tried every AI design tool so you don't have to",
    "Building a faceless YouTube channel with AI",
    "AI vs human: who makes better Etsy listings?",
    "How I went from 0 to 21 Etsy listings in 24 hours",
    "The truth about AI print on demand in 2025",
    "I automated my entire business on a MacBook Air",
    "Day 7: Here's what actually made money",
    "AI tools tier list for Etsy sellers",
    "How to start an AI business with $0",
    "I made AI design 100 products overnight",
    "The AI business nobody talks about",
    "From idea to Etsy listing in 10 minutes using AI",
    "I quit trying to code and let AI do it instead",
]
TEMPLATE_CONTENT = (
    "HOOK (0-3 seconds): [one shocking or curious statement]\n"
    "PROBLEM (3-30 seconds): [what problem this video solves]\n"
    "STORY (30s-3min): [what happened, be honest and specific]\n"
    "REVEAL (3-5min): [the result or lesson]\n"
    "CTA (last 10 seconds): [subscribe + what's coming next]\n"
)


def build_channel_structure() -> None:
    BaseDirs = [BASE_DIR] + [BASE_DIR / subdir for subdir in SUBDIRS]
    for path in BaseDirs:
        path.mkdir(parents=True, exist_ok=True)

    ideas_path = BASE_DIR / "ideas.txt"
    if not ideas_path.exists():
        ideas_path.write_text("\n".join(IDEAS) + "\n", encoding="utf-8")

    template_path = BASE_DIR / "script_template.txt"
    if not template_path.exists():
        template_path.write_text(TEMPLATE_CONTENT, encoding="utf-8")

    created = [str(path.relative_to(BASE_DIR)) for path in BaseDirs]
    print("YouTube channel setup complete. Created the following paths:")
    for entry in created:
        print(f"- {entry}")
    print(f"- ideas.txt")
    print(f"- script_template.txt")


def _safe_filename(title: str) -> str:
    value = title.strip().replace(" ", "_")
    value = "".join(ch for ch in value if ch.isalnum() or ch in {"_", "-"})
    return value[:120] or "untitled"


def generate_script(title: str) -> None:
    """Generate a simple video script from a title and save it to the scripts folder."""
    build_channel_structure()
    section_text = {
        "HOOK (0-3 seconds)": f"{title} — here is the surprising truth you need to know right away.",
        "PROBLEM (3-30 seconds)": f"Many people want to build an AI business, but they don't know how to start or how to make it profitable.",
        "STORY (30s-3min)": f"I started with this idea: '{title}'. I used the AI Factory system to generate ideas, create listings, and track results in a local workflow.",
        "REVEAL (3-5min)": f"The result was a clear process: use AI to move from idea to product, then learn from real performance instead of guessing.",
        "CTA (last 10 seconds)": "Subscribe for the next update and watch how I turn this AI business into repeatable revenue.",
    }

    contents = []
    for label, text in section_text.items():
        contents.append(f"{label}: {text}\n")
    script_text = "\n".join(contents)

    script_name = f"{_safe_filename(title)}.txt"
    script_path = BASE_DIR / "scripts" / script_name
    script_path.write_text(script_text, encoding="utf-8")
    print(f"Generated script for: {title}")
    print("\n" + script_text)


if __name__ == "__main__":
    build_channel_structure()
