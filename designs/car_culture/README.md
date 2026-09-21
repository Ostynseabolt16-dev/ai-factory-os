# Car culture print files (brand-free)

Type-first joke tees for the car-adjacent niches: **no brand wordmarks, model names, or logos**, so none of the Corvette IP risk. Composed locally with Pillow + Anton — **no OpenAI spend**.

## Wave 1 SKUs

| SKU | Copy | Upload file |
|-----|------|-------------|
| Third Pedal (manual) | MY ANTI-THEFT DEVICE / **THIRD PEDAL** / GOOD LUCK | `manual_third_pedal_UPLOAD_TO_PRINTIFY.png` |
| 5 Minute Job (garage) | IT WAS SUPPOSED TO BE A / **5 MINUTE JOB** / THAT WAS SATURDAY | `garage_five_minute_job_UPLOAD_TO_PRINTIFY.png` |
| The Cone Hit Me (autocross) | I DIDN'T HIT THE CONE / **THE CONE** / HIT ME | `autocross_cone_hit_me_UPLOAD_TO_PRINTIFY.png` |

Listing copy: `../listings/CAR_CULTURE_WAVE1.md` · Plan + launch gate: `../listings/NICHE_PORTFOLIO.md`

**Dark shirts only** (Black, Navy, Charcoal) — the type is white + accent and vanishes on light colors.

## Regenerate

```bash
python3 scripts/compose_type_first_tee.py            # all SKUs
python3 scripts/compose_type_first_tee.py third_pedal # one SKU
python3 scripts/compose_type_first_tee.py --list
```

Add a new SKU by appending to `SKUS` in `scripts/compose_type_first_tee.py` — lines, which line is the hero, and the accent color. The export runs `prepare_printify_exports.py --threshold 235 --no-knock-out-counters` (the accent line reads as dark ink, so counter knock-out would delete the white lines).
