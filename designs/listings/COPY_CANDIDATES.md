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

### Batch 1 — Oct 27, 2026 (16 screenshots)

**Batch-level read:** the three highest-scoring items here are **formats**, not jokes. Several of these
shirts share a structure we already have sales proof for — **small front hit + big back print**
(C5 Blueprint front/back sold; the Yellow C5 2-sided hoodie at $51.99 is our single biggest order).
Also note **half this batch is TikTok Shop / Temu goods priced $3.39–$7.77**. Their jokes convert at
that price because the price *is* the offer. Do not lift one of those jokes onto a $21.99 listing and
expect it to convert — we lose that fight on price and win on art, niche, and front/back value.

---

### CAND-001 — Red gothic chest script on black crew ("Hellboy" look) — **owner favorite**
Source: Instagram story, person wearing it; song tag "Hell boy — Lil Peep". No sales data.
Scores: demand 1 · fit 2 · IP 3 · thumbnail 1 · cost 3 · margin 3 = **13**
Verdict: **HOLD — upgrade to BUILD by fixing one thing**

The look is genuinely good and it is nearly free for us to make: one small word in red
blackletter/tattoo script, centered high on the chest of a black crewneck. It reads as real
streetwear instead of print-on-demand, and **we already own the gothic lettering style** — it's one
of our three proven formats.

Two problems:

- **The word "Hellboy" is out.** It's a Lil Peep mixtape title *and* a Dark Horse Comics character.
  Two separate trademark owners, and this exact shirt is Peep merch. Auto-SKIP on wording.
- **A small chest print photographs badly in the Etsy grid.** This is the same CTR failure already
  logged against the C8 listing. At thumbnail size a 4-inch red script on black nearly disappears.

**Fix that promotes it to BUILD (15):** make it **front + back** — small red script chest hit, big
back print. That's the structure in CAND-006 and CAND-015, and the structure our two biggest orders
used. The back print carries the thumbnail, the chest hit sells the shirt in person.

Our version: red blackletter chest script using **our own wording** — a generation tag (`C5`, `C7`),
or enthusiast language we already write (`SMALL BLOCK`, `BUILT WILD`, `BORN WILD`). No `CORVETTE`,
no `VETTE`, no crossed flags. Back print: existing collection car art.
**Do NOT make:** the word Hellboy, any Lil Peep lyric, the comic character, or an angel/cross motif
traced from Peep merch.
**Next:** compose locally from existing gothic type — no OpenAI spend needed.

---

### CAND-002 — "WRONG HOLE" pickleball gag — *from owner's own notes*
Source: owner idea list. No external data, but the adjacent joke category is **our own proven seller**.
Scores: demand 2 · fit 3 · IP 3 · thumbnail 3 · cost 3 · margin 3 = **17**
Verdict: **BUILD — highest score in the batch**

This is the single best idea in everything sent. It is the *exact* format that produced our only
pickleball sale: a short type-first line gag on a dark shirt. IT WAS IN sold; the two illustrated
pickleball shirts (Soft Serve, Eyes Up Here) are still at zero. The data says type gag, not art.

Zero IP risk, zero build cost, reads instantly at thumbnail size, and innuendo-adjacent pickleball
humor is squarely inside the "dinking problem" search category we already know is hot.

Our version: huge stacked type, ball below, white/lime/white stack — same system as Dinking Problem,
so `scripts/compose_pickleball_dinking_problem.py` is the template.
**Do NOT make:** anything anatomically explicit; keep it to the court joke so Etsy doesn't flag it.
**Next:** write the listing `.md`, compose locally, eBay first at **$20.99** S–XL.

---

### CAND-011 — Vintage band-tee photo collage ("MILF / Man I Love Fish")
Source: TikTok Shop, 96 likes, 24 saves.
Scores: demand 2 · fit 2 · IP 3 · thumbnail 3 · cost 2 · margin 3 = **15**
Verdict: **BUILD — as a format, applied to Corvettes**

Ignore the fishing pun; copy the **layout**. Big serif word across the top, several photo-real
subjects collaged below, washed white tee, 90s band-merch feel. It's a completely different visual
system from our gothic and blueprint lines, aimed at the same buyer — the tags we already use are
"gift for him", "car guy gift", "gearhead gift", and fishing/car gift shoppers are the same person.

This also gives us a way to reuse car renders we already paid to generate, which is the cheapest new
listing available to us right now.

Our version: a C5 or C7 "vintage tour tee" — big serif generation word up top, three to five of our
existing car renders collaged below, optional year range as a tour-date line.
**Do NOT make:** the MILF acronym gag, or any real band's logo/tour-date lockup.
**Next:** compose locally from existing masters in `designs/corvette/`.

---

### Auto-SKIP — brand wordmarks and licensed characters

These four had the strongest social signal in the batch and are the ones we most clearly cannot
touch. Worth knowing *why* each is unusable so we don't revisit them:

| # | Shirt | Signal | Why it's out |
|---|-------|--------|--------------|
| CAND-005 | CAPTAIN SAVE-A-HO | **5,003 likes · 604 saves · 1,501 shares** — strongest in batch | Superman shield pastiche → DC/Warner. Phrase is also an E-40 song. |
| CAND-004 | SHOW ME YOUR BUSCH | 2,290 likes · 281 saves | Busch Light wordmark + can art reproduced. |
| CAND-006 | Modelo alien "Humans Aren't Real" | 34 likes | Modelo wordmark. (Front/back structure noted — see CAND-001.) |
| CAND-013 | Benadryl "hat man" | $3.39, 5★ | Kenvue brand logo reproduced, plus drug-reference humor. |

The beer-pun *category* (CAND-004) does show real demand, and the owner's notes list has "a reason to
drink today" in the same family — that's buildable with **no brand**, just not as a Busch clone.

---

### SKIP

- **CAND-007 — BIG BOOTY WITCHES.** Someone's signed original drawing, nude figures, 1 like, posted
  Oct 2024. Copying a named artist's piece is the one thing we never do, and Etsy will flag the art.
- **CAND-008 — "funny space shirts" search grid.** Not a design, a search result — and what it shows
  is a commodity niche selling at **$13 on TeePublic** with Star Wars/Yoda shirts in the results.
  We cannot win a $13 race, and we have no space audience.
- **CAND-009 — "She neon on my Genesis til I Evangelion," $7.77.** Licensed anime in the hook and a
  price point we can't touch.
- **CAND-012 — "Outta Spells But Not Outta Shells," $4.99.** Score **9**. Good pun and a real
  wizard/hunting crossover audience, but it needs illustration we'd have to generate (OpenAI spend
  we don't have) to compete against a $4.99 listing. Wrong economics.
- **Heaven's Gate program** (owner notes) — cult/mass-suicide reference. Not a joke we put our shop
  name on.
- **Bay Area shirts** (owner notes) — too broad and we have no Bay Area audience or local channel.

---

### HOLD — good, but parked with the blocker named

- **CAND-003 — "FUN FACT / I DON'T CARE."** Score **11**. Perfect thumbnail read, pure type, zero IP,
  but only 5 likes and the phrase is completely saturated with no angle for us to differentiate.
- **CAND-010 — "I had no idea these tattoos were permanent," $5.80.** Score **11**. Genuinely funny,
  pure type, no IP — but it's an attitude tee for a non-car audience being dumped at $5.80.
- **CAND-014 — "Buy a man eat fish, he day, teach fish man to a lifetime," $3.99.** Score **12**. The
  value here is the **scrambled-proverb format** — it's a reusable joke engine with no IP, and a
  car-guy version would score higher than this fishing one. Worth revisiting after CAND-002.
- **CAND-015 — Y2K gothic wings, small front + big back.** Score **12**. 697 likes, 343 saves, and
  **zero IP** — the rare high-signal item we could legally build. Blocked on illustration cost
  (detailed wings), and it aims at a fashion buyer rather than our car/gag buyer. Its real
  contribution to this batch is proving the front/back structure.
- **"Follow me to pickleball" bumper sticker** (owner notes) — mild and on-niche, but weaker than
  CAND-002. Queue behind it.
- **Trebuchets / catapults** (owner notes) — real engineering-humor niche, very type-friendly, no IP.
  Genuinely interesting but it's a cold-start audience; park until the pickleball line is working.

---

### CAND-017 — "maybe the turtles needed the straws" (cartoon turtles + powder lines)
Source: product image on heather blue tee, no marketplace or sales data supplied.
Scores: demand 1 · fit 0 · IP 2 · thumbnail 3 · cost 0 · margin 2 = **8**
Verdict: **SKIP — but the joke engine is worth keeping**

The gag is genuinely well built: it takes the save-the-turtles straw ban, which everybody recognizes,
and flips it. Bold outlined type, bright palette, reads clean at thumbnail size. Nothing wrong with
the craft.

It fails on our constraints, not on quality:

- **Wrong audience entirely.** We sell Corvette graphics and pickleball court gags to a gift-for-him
  buyer. Cute-animal stoner humor shares no tags, no search terms, and no shoppers with that.
- **It's the illustrated-character trap we already paid for twice.** Soft Serve (illustrated cone
  character) and Eyes Up Here (illustrated) are both still at **zero sales**. IT WAS IN, pure type,
  is the one that sold. `designs/` is also full of unsold cute-animal renders from the May era.
  Every time this shop has bought character art, it has not converted.
- **We can't build it.** Full-color cartoon character art means an OpenAI run, which is blocked on
  credits. Our local Pillow pipeline composes type, not illustration.
- **Content risk on a shop with a live strike.** The powder-lines gag is a drug reference on a
  platform that prohibits drug paraphernalia. Joke tees usually survive, but we already took one
  Etsy takedown in July and shouldn't spend a second strike on an off-brand design.

**Keep this instead:** the structure — *take a wholesome cause everyone knows, flip it* — is a
reusable joke engine that costs nothing in pure type. It sits next to the scrambled-proverb format
in CAND-014 as a template to point at a niche we actually sell to.
**Do NOT make:** this turtle art, any version of it, or the straw-in-the-nose viral image it riffs on.

---

### Build order out of this batch

1. **List Dinking Problem** — print file has been export-ready since Jul 21 and still isn't live.
   Zero design work. Do this before building anything new.
2. **CAND-002 Wrong Hole** — same compose script, same proven format.
3. **CAND-001 red gothic chest script, front + back** — owner's pick, fixed for thumbnail.
4. **CAND-011 vintage collage Corvette** — reuses car art already paid for.

---

## Standing context for whoever scores these

**Proven for this shop:** Corvette C4 / C5 / C7 / C8 graphics, blueprint front+back, gothic text +
side car, and minimal type-first pickleball gags. Those three formats produced every sale in
`sales_log.csv`.

**Not proven:** full-AI photoreal shirt art, line-art C8, lifestyle hero thumbnails, hoodies
beyond the Yellow C5 pair, and every cute-animal/sticker concept in `designs/`.

**Known cost floor:** a $19 tee nets about $4.82 after eBay fees and Printify. $20.99+ on S-XL is
the working minimum for new SKUs.
