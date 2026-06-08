#!/usr/bin/env python3
"""Build youtube/client_secrets.json from values copied out of Google Cloud Console."""

from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "client_secrets.json"


def main() -> None:
    print("=" * 60)
    print("Cozy Orbit — OAuth setup (no download button needed)")
    print("=" * 60)
    print()
    print("Google only shows the secret ONCE. Get it from ONE of these:")
    print("  A) Create a NEW Desktop client → copy from the popup")
    print("  B) Open your client → Client secrets → Add client secret")
    print()
    client_id = input("Paste Client ID (ends with .apps.googleusercontent.com): ").strip()
    client_secret = input("Paste Client secret (starts with GOCSPX-): ").strip()
    project_id = input("Project ID (optional, press Enter to skip): ").strip() or "cozy-orbit"

    if not client_id.endswith(".apps.googleusercontent.com"):
        raise SystemExit("Client ID does not look right. Copy it from Google Cloud.")
    if not client_secret.startswith("GOCSPX-"):
        raise SystemExit("Client secret does not look right. It must start with GOCSPX-")

    data = {
        "installed": {
            "client_id": client_id,
            "project_id": project_id,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": client_secret,
            "redirect_uris": ["http://localhost"],
        }
    }
    OUT.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print()
    print(f"Wrote {OUT}")
    print("Now run your upload command.")


if __name__ == "__main__":
    main()
