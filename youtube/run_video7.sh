#!/usr/bin/env bash
# Video 7: rainy window + library_rain.mp3 → upload
set -euo pipefail
cd /Users/ostynseabolt/ai
source .venv/bin/activate

IMAGE="designs/rainy_window_library_books.png"
AUDIO="youtube/assets/audio/library_rain.mp3"
OUTPUT="youtube/exported/video7_library_rain.mp4"
META="youtube/titles/ambient_video_7.txt"

if [[ ! -f "$IMAGE" ]]; then
  echo "Missing image: $IMAGE"
  echo "Generate with youtube/generate_video7_image.py or save your own PNG there."
  exit 1
fi

python youtube/make_video.py "$IMAGE" "$AUDIO" --output video7_library_rain.mp4
python youtube/upload_video.py "$OUTPUT" "$META" --privacy public
