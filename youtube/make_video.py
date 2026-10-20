from __future__ import annotations

import argparse
import math
from pathlib import Path

from moviepy import AudioFileClip, ImageClip, concatenate_audioclips


OUTPUT_DIR = Path("/Users/ostynseabolt/ai/youtube/exported")
TARGET_DURATION = 2 * 60 * 60
SUPPORTED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".ogg"}


def build_video(image_path: Path, audio_path: Path, output_path: Path) -> None:
    print(f"Looking for image: {image_path}")
    if not image_path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")
    print(f"Looking for audio: {audio_path}")
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    if audio_path.suffix.lower() not in SUPPORTED_AUDIO_EXTENSIONS:
        raise ValueError("Audio must be one of: .mp3, .wav, .m4a, .aac, .ogg")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("Loading image clip...")
    image_clip = ImageClip(str(image_path))
    width, height = image_clip.size

    print("Loading audio clip...")
    audio_clip = AudioFileClip(str(audio_path))
    print(f"Audio duration: {audio_clip.duration:.2f} seconds")
    if audio_clip.duration <= 0:
        raise ValueError("Audio file has invalid duration")

    if audio_clip.duration >= TARGET_DURATION:
        looped_audio = audio_clip.subclip(0, TARGET_DURATION)
    else:
        loops_needed = math.ceil(TARGET_DURATION / audio_clip.duration)
        print(f"Looping audio {loops_needed} times to reach target duration")
        looped_audio = concatenate_audioclips([audio_clip] * loops_needed).subclipped(0, TARGET_DURATION)

    print("Building video clip with slow zoom...")
    zoom_factor = 1.08
    def zoom(t):
        return 1 + (zoom_factor - 1) * (t / TARGET_DURATION)

    video_clip = (
        image_clip
        .with_duration(TARGET_DURATION)
        .resized(lambda t: zoom(t))
        .cropped(x_center=width / 2, y_center=height / 2, width=width, height=height)
        .with_fps(24)
        .with_audio(looped_audio)
    )

    print(f"Rendering MP4 to {output_path}...")
    video_clip.write_videofile(
        str(output_path),
        codec="libx264",
        audio_codec="aac",
        fps=24,
        bitrate="3000k",
        preset="medium",
        threads=4,
        logger="bar",
    )

    print("Finished rendering video.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a 2-hour video from a static image and audio file.")
    parser.add_argument("image", help="Path to the image file")
    parser.add_argument("audio", help="Path to the audio file")
    parser.add_argument(
        "--output",
        help="Optional output video filename (defaults to exported/video.mp4)",
        default="video.mp4",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    image_path = Path(args.image.strip()).expanduser().resolve()
    audio_path = Path(args.audio.strip()).expanduser().resolve()
    output_path = Path(args.output.strip()).expanduser()
    if not output_path.is_absolute():
        output_path = OUTPUT_DIR / output_path
    output_path = output_path.resolve()
    build_video(image_path, audio_path, output_path)
