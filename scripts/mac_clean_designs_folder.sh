#!/usr/bin/env bash
# Mac-only: clean CozyOrbit designs folder.
# Deletes May sticker / cute / factory junk and creates niche folders.
#
# Usage (on MacBook):
#   cd ~/ai
#   bash scripts/mac_clean_designs_folder.sh
#
# Safe: only deletes known junk filenames. Keeps listings/, fonts/, and any
# corvette_*/c*_collection*/pickleball_* files (moves them into folders).

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DESIGNS="$ROOT/designs"

if [[ ! -d "$DESIGNS" ]]; then
  echo "No designs folder at $DESIGNS"
  exit 1
fi

cd "$DESIGNS"
echo "Cleaning: $DESIGNS"

mkdir -p corvette pickleball couple_faces fonts listings

# --- delete sticker / cute / factory junk (same set we removed from git) ---
rm -f \
  "ai 123.png" \
  cute_*.png \
  emotionally_exhauste.png \
  fancy_*.png \
  happy_ramen_bowl_and.png \
  introverted_orange_c.png \
  lego_*.png \
  oteer_Cute_Catronaut.png \
  product_*.png \
  social_anxiety_*.png \
  2>/dev/null || true

# --- move Corvette assets into corvette/ ---
shopt -s nullglob
for f in corvette_*.png corvette_*.jpg \
         c3_*.png c4_*.png c5_*.png c6_*.png c7_*.png c8_*.png \
         cozy_orbit_etsy_*.png; do
  [[ -f "$f" ]] || continue
  mv -n "$f" corvette/
  echo "→ corvette/$f"
done

# --- move pickleball assets into pickleball/ ---
for f in pickleball_*.png pickleball_*.jpg; do
  [[ -f "$f" ]] || continue
  mv -n "$f" pickleball/
  echo "→ pickleball/$f"
done

# --- move couple race-car faces into couple_faces/ ---
for f in couple_race_*.png couple_race_*.jpg couple_sky_*.png couple_sky_*.jpg; do
  [[ -f "$f" ]] || continue
  mv -n "$f" couple_faces/
  echo "→ couple_faces/$f"
done
shopt -u nullglob

echo
echo "Done. designs/ should now look like:"
echo "  corvette/   pickleball/   couple_faces/   listings/   fonts/"
echo
echo "McQueen-style tees (IP-safe — do NOT use Disney names in listings):"
echo "  couple_faces/couple_race_red_face_UPLOAD_TO_PRINTIFY.png"
echo "  couple_faces/couple_sky_blue_face_UPLOAD_TO_PRINTIFY.png"
echo "  listings/COUPLE_RACE_CAR_FACES.md"
ls -la
