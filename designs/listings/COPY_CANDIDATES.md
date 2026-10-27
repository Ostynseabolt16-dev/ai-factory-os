# Copy Candidates — screenshot intake + verdicts

> **Purpose:** owner sends screenshots of shirts seen in the wild (Etsy, eBay, TikTok, Amazon, Instagram).
> Agent scores each one and returns **BUILD / HOLD / SKIP** with a reason.
> **Working rule (from `PICKLEBALL_WAVE2.md`):** steal the *concept category*, invent new wording, layout, and art.
> Never trace, re-upload, or re-type someone else's artwork.

---

## How to send them

**Easiest:** attach the images directly in chat and say "copy candidates" — no file paths needed.

**If you'd rather drop files:** put them in `designs/research/screenshots/` and name them so the
source is obvious, e.g. `etsy_dink_hoodie_01.png`, `tiktok_vette_sunset_02.jpg`.

**Helps a lot if you include (one line each, best guess is fine):**

- Where you saw it (Etsy / eBay / TikTok / Amazon / in person)
- Any visible proof of demand — review count, "X sold", bestseller badge, view count, price
- Why it caught your eye (the joke? the layout? the car? the colors?)

If you only have the picture, send it anyway. Missing demand data just caps the score — see
**Demand proof** below.

---

## Scoring rubric (max 20)

Each candidate gets scored on six axes. Verdict thresholds are at the bottom.

| # | Axis | 0 | 1 | 2 | 3 |
|---|------|---|---|---|---|
| 1 | **Demand proof** | no signal, just looks nice | one soft signal (lots of likes, crowded search) | real signal (review count, "X sold", bestseller badge) | hard signal **in a niche we already sell** (Corvette, pickleball gag) |
| 2 | **Niche fit** | unrelated niche, new audience from scratch | adjacent (other car marque, other racket sport) | same audience, new angle | direct variant of a proven seller (C4/C5/C7/C8, type-first pickleball gag) |
| 3 | **IP risk** (see hard rules) | brand wordmark / logo / parody of a real brand | recognizable licensed character or team | real car, no marks, generic wording | pure typography or our own art, nothing borrowable |
| 4 | **Thumbnail read** | needs zoom to get it | reads at full size only | reads at Etsy grid size | reads instantly, joke lands in under a second |
| 5 | **Build cost** | needs OpenAI gen we can't fund right now | needs a new car render | local compose + existing art | pure type — `compose_*`-style script, no spend |
| 6 | **Margin at our price** | under $4 net at a realistic price | $4-5 net | $5-8 net | $8+ net, or hoodie-tier pricing holds |

**Verdict:**

| Score | Verdict | Meaning |
|-------|---------|---------|
| 15-20 | **BUILD** | queue it; write the listing `.md`, then compose |
| 10-14 | **HOLD** | good idea, wrong moment — park it with the blocker named |
| 0-9 | **SKIP** | log the reason so we don't re-litigate it in three weeks |

**Automatic SKIP regardless of score** if it trips any hard rule below.

---

## Hard rules (these override the score)

- **No brand wordmarks.** `CORVETTE`, `CHEVROLET`, crossed flags, `Z06`, `STINGRAY` as set type.
  This is exactly what got the Yellow C5 Etsy listing pulled in July.
- **No brand parody.** No swoosh/"JUST DUI IT" class of joke, no logo riffs.
- **No licensed characters, teams, or celebrity likenesses.**
- **No tracing or re-typing the screenshot's layout.** New wording, new arrangement, our fonts.
  If the only thing that makes it work is their exact composition, it's a SKIP.
- **Dark artwork → light shirts only** (White, Natural, Sport Grey). Light/type-only art → dark shirts.
- **No OpenAI `generate_*.py` runs** without an explicit spend OK from the owner.

---

## What a finished verdict looks like

Each candidate gets an entry in this shape, appended to the log below:

```
### CAND-001 — <short name>
Source: Etsy, 1.2k sales, $24.99
Scores: demand 3 · fit 3 · IP 2 · thumbnail 3 · cost 3 · margin 2 = 16
Verdict: BUILD
Our version: <the actual wording/layout change that makes it ours>
Do NOT make: <the specific clone layout we're avoiding>
Next: write listing .md -> compose locally -> eBay first at $XX.99
```

---

## Verdict log

_(empty — first batch of screenshots lands here)_

---

## Standing context for whoever scores these

**Proven for this shop:** Corvette C4 / C5 / C7 / C8 graphics, blueprint front+back, gothic text +
side car, and minimal type-first pickleball gags. Those three formats produced every sale in
`sales_log.csv`.

**Not proven:** full-AI photoreal shirt art, line-art C8, lifestyle hero thumbnails, hoodies
beyond the Yellow C5 pair, and every cute-animal/sticker concept in `designs/`.

**Known cost floor:** a $19 tee nets about $4.82 after eBay fees and Printify. $20.99+ on S-XL is
the working minimum for new SKUs.
