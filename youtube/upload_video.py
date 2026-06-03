from __future__ import annotations

import argparse
import os
import re
import tempfile
import time
from datetime import datetime
from pathlib import Path

import httplib2
from PIL import Image
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_httplib2 import AuthorizedHttp
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

BASE_DIR = Path("/Users/ostynseabolt/ai/youtube")
CLIENT_SECRETS_CANDIDATES = [
    BASE_DIR / "client_secrets.json",
    BASE_DIR.parent / "client_secrets.json",
]
TOKEN_FILE = BASE_DIR / "token.json"
LOG_FILE = BASE_DIR / "production_log.txt"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
# Large 2-hour uploads need long per-chunk timeouts (default is too short on Wi‑Fi).
HTTP_TIMEOUT_SEC = 3600
UPLOAD_CHUNK_BYTES = 4 * 1024 * 1024
MAX_CHUNK_RETRIES = 15
THUMBNAIL_MAX_BYTES = 2 * 1024 * 1024


def parse_metadata(path: Path) -> dict[str, str | list[str]]:
    text = path.read_text(encoding="utf-8")
    sections: dict[str, str] = {}
    current: str | None = None
    lines: list[str] = []

    def flush() -> None:
        if current is not None:
            sections[current] = "\n".join(lines).strip()

    title_aliases = {"TITLE", "FINAL YOUTUBE TITLE"}
    desc_aliases = {"DESCRIPTION", "DESC"}
    tag_aliases = {"TAGS", "TAG"}

    for raw in text.splitlines():
        if not raw.strip():
            continue
        label = raw.strip()
        if label.endswith(":"):
            key = label[:-1].strip().upper()
            if key in title_aliases | desc_aliases | tag_aliases | {"THUMBNAIL PROMPT", "AUDIO SEARCH TERM"}:
                flush()
                if key in title_aliases:
                    current = "TITLE"
                elif key in desc_aliases:
                    current = "DESCRIPTION"
                elif key in tag_aliases:
                    current = "TAGS"
                else:
                    current = key
                lines = []
                continue
        lines.append(raw)
    flush()

    title = str(sections.get("TITLE", "")).strip()
    description = str(sections.get("DESCRIPTION", "")).strip()
    tags_raw = str(sections.get("TAGS", "")).strip()
    tags = [tag.strip() for tag in re.split(r",|\n", tags_raw) if tag.strip()]
    if not title or not description:
        raise ValueError(f"Metadata file must include title and description: {path}")
    return {"title": title, "description": description, "tags": tags[:30]}


def find_client_secrets() -> Path:
    for path in CLIENT_SECRETS_CANDIDATES:
        if not path.exists():
            continue
        head = path.read_text(encoding="utf-8", errors="ignore")[:20].strip()
        if head.startswith("{"):
            return path
        raise ValueError(
            f"{path} is not a valid OAuth JSON file (looks like a saved web page).\n"
            "In Google Cloud → Credentials → your Desktop OAuth client → click the "
            "download arrow (⬇) and save the .json file — do not Save Page from the browser."
        )
    raise FileNotFoundError(
        "Missing client_secrets.json\n"
        "Save the downloaded OAuth Desktop JSON to:\n"
        f"  {CLIENT_SECRETS_CANDIDATES[0]}\n"
        "Google Cloud → Credentials → OAuth 2.0 Client IDs → your Desktop client → Download JSON"
    )


def get_youtube_service():
    client_secrets = find_client_secrets()

    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(client_secrets), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    http = httplib2.Http(timeout=HTTP_TIMEOUT_SEC)
    # YouTube resumable uploads use HTTP 308; httplib2 must not treat it as a redirect.
    http.redirect_codes = set(http.redirect_codes) - {308}
    authorized = AuthorizedHttp(creds, http=http)
    return build("youtube", "v3", http=authorized)


def prepare_thumbnail_for_upload(thumbnail_path: Path) -> tuple[Path, Path | None]:
    """Use original file if under 2MB; otherwise write a compressed temporary JPEG."""
    if not thumbnail_path.exists():
        raise FileNotFoundError(f"Thumbnail not found: {thumbnail_path}")

    size = thumbnail_path.stat().st_size
    if size <= THUMBNAIL_MAX_BYTES:
        return thumbnail_path, None

    print(
        f"Thumbnail {thumbnail_path.name} is {size / (1024 * 1024):.2f} MB; "
        "compressing to JPEG for YouTube (2 MB limit)...",
        flush=True,
    )
    image = Image.open(thumbnail_path)
    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")

    fd, tmp_name = tempfile.mkstemp(suffix=".jpg", prefix="yt_thumb_")
    temp_path = Path(tmp_name)
    try:
        os.close(fd)
        width, height = image.size
        image.save(temp_path, "JPEG", quality=85, optimize=True)
        while temp_path.stat().st_size > THUMBNAIL_MAX_BYTES and max(width, height) > 480:
            width = int(width * 0.85)
            height = int(height * 0.85)
            resized = image.resize((width, height), Image.Resampling.LANCZOS)
            resized.save(temp_path, "JPEG", quality=85, optimize=True)

        compressed_mb = temp_path.stat().st_size / (1024 * 1024)
        print(f"Using compressed thumbnail ({compressed_mb:.2f} MB): {temp_path.name}", flush=True)
        return temp_path, temp_path
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


def log_upload(title: str, video_id: str, privacy: str) -> None:
    timestamp = datetime.now().replace(microsecond=0).isoformat()
    with LOG_FILE.open("a", encoding="utf-8") as log:
        log.write(f"{timestamp} | {title} | uploaded | {video_id} | {privacy}\n")


def upload_video(
    video_path: Path,
    metadata_path: Path,
    thumbnail_path: Path | None,
    privacy: str,
) -> str:
    meta = parse_metadata(metadata_path)
    youtube = get_youtube_service()

    body = {
        "snippet": {
            "title": meta["title"],
            "description": meta["description"],
            "tags": meta["tags"],
            "categoryId": "10",
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        },
    }

    size_mb = video_path.stat().st_size / (1024 * 1024)
    media = MediaFileUpload(
        str(video_path),
        mimetype="video/mp4",
        resumable=True,
        chunksize=UPLOAD_CHUNK_BYTES,
    )

    print(f"Uploading {video_path.name} ({size_mb:.0f} MB) — keep Mac awake on Wi‑Fi...")
    print("Starting upload (first % may take 1–2 min on slow Wi‑Fi — do not press Ctrl+C)...", flush=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    chunk_errors = 0
    last_pct = -1
    while response is None:
        try:
            status, response = request.next_chunk()
            chunk_errors = 0
            if status:
                pct = int(status.progress() * 100)
                if pct != last_pct:
                    print(f"Upload progress: {pct}%", flush=True)
                    last_pct = pct
            elif last_pct < 0:
                print("Upload progress: 0% (connected, sending data...)", flush=True)
                last_pct = 0
        except (TimeoutError, OSError) as err:
            chunk_errors += 1
            if chunk_errors > MAX_CHUNK_RETRIES:
                raise RuntimeError(
                    f"Upload failed after {MAX_CHUNK_RETRIES} retries: {err}\n"
                    "Try: stronger Wi‑Fi, Ethernet, or run again (resumable upload continues)."
                ) from err
            wait = min(60, 2**chunk_errors)
            print(f"Network hiccup ({err!s}). Retry {chunk_errors}/{MAX_CHUNK_RETRIES} in {wait}s...", flush=True)
            time.sleep(wait)

    video_id = response["id"]
    print(f"Upload complete. Video ID: {video_id}")
    print(f"Studio link: https://studio.youtube.com/video/{video_id}/edit")

    if thumbnail_path:
        upload_thumbnail, temp_thumbnail = prepare_thumbnail_for_upload(thumbnail_path)
        try:
            print(f"Setting thumbnail: {upload_thumbnail.name}")
            youtube.thumbnails().set(videoId=video_id, media_body=str(upload_thumbnail)).execute()
        finally:
            if temp_thumbnail is not None:
                temp_thumbnail.unlink(missing_ok=True)

    log_upload(str(meta["title"]), video_id, privacy)
    return video_id


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Upload a video to YouTube using a metadata .txt file.")
    parser.add_argument("video", help="Path to MP4 file")
    parser.add_argument("metadata", help="Path to titles/*.txt metadata file")
    parser.add_argument("--thumbnail", help="Path to thumbnail image (png/jpg)")
    parser.add_argument(
        "--privacy",
        choices=["private", "unlisted", "public"],
        default="private",
        help="YouTube privacy (default: private so you can check first)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    video_path = Path(args.video).expanduser().resolve()
    metadata_path = Path(args.metadata).expanduser().resolve()
    thumbnail_path = Path(args.thumbnail).expanduser().resolve() if args.thumbnail else None

    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata not found: {metadata_path}")

    upload_video(video_path, metadata_path, thumbnail_path, args.privacy)
