# Corvette design assets

All Corvette masters, Printify uploads, and Etsy shop branding live **here**.

```
designs/corvette/
  corvette_*_UPLOAD_TO_PRINTIFY.png
  c*_collection*.png
  c*_variant_B*.png
  cozy_orbit_etsy_profile_500.png
  cozy_orbit_etsy_banner_3360x840.png
  banner/                    (optional source cars)
```

## Mac sync

If PNGs are missing in this cloud/GitHub copy, they are on the Mac:

```bash
cd ~/ai
# move any leftover flat files into the corvette folder:
mkdir -p designs/corvette
mv designs/corvette_*.png designs/corvette/ 2>/dev/null
mv designs/c[3-8]_*.png designs/corvette/ 2>/dev/null
mv designs/cozy_orbit_etsy_*.png designs/corvette/ 2>/dev/null
```

Listing copy stays in `../listings/` (e.g. `C7_VARIANT_B.md`, `C5_TORCH_RED.md`).

Do **not** put pickleball, couple faces, or sticker files here.
