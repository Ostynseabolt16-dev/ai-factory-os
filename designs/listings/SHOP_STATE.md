# CozyOrbitPrints — Shop State (source of truth)

**Etsy shop:** https://www.etsy.com/shop/CozyOrbitPrints  
**Last updated:** 2026-10-27 (Etsy + eBay P&L reconciled; eBay 8 orders = 6 apparel + 2 LEGO; copy candidates in `COPY_CANDIDATES.md`)

Read this file + `sales_log.csv` + `COZY_ORBIT_HANDOFF.md` at the start of any new agent chat to avoid hallucinating order/design state.

> **NOT kawaii stickers.** Live business = CozyOrbitPrints Corvette apparel (Etsy + eBay + Printify). GitHub `ai-factory-os` is stale May factory scaffolding — ignore it unless explicitly working on factory code.

---

## Oct 27 update — dry spell + copy-candidate review

Owner reports **no recent sales on Etsy or eBay** and is sending screenshots of shirts to evaluate
for "which ones should we copy."

| Item | Status |
|------|--------|
| **Last logged sale in `sales_log.csv`** | **Jul 17** — but Etsy shows **3 orders / $164.62 in the last 30 days** (Kids Play Mat Oct 14; Corvette C5 Blueprint Poster ~Oct 22; a 3-item order ~Oct 22). The log is behind by at least these three. Back-fill from Etsy Orders. |
| **Headline** | Etsy reports **$540.21 net profit** over 12 months, but that **excludes Printify ($1,008.40)**. Etsy POD all-in **−$156.78**; eBay POD **~breakeven** on ~10 apparel orders; **2 LEGO sales are separate**. Combined POD **≈ −$100 to −$140** (fees TBD). See true-P&L block. |
| **eBay (refreshed Oct 27)** | **8 orders total** — **6 Printify apparel · 2 LEGO resale** (exclude LEGO from apparel P&L). Hub: 29 active · 4 unsold · **90-day sales $273.58**. See eBay block below. |
| **Etsy Ads numbers** | **Refreshed Oct 27** — see the real-numbers block below. The Jun 26 snapshot further down is superseded. |
| **eBay still needed** | Total **earnings after fees** from eBay Payments (not just buyer-paid subtotals). Promoted-listing ad % on the C7 line. |
| **Dinking Problem** | **Sold on eBay Aug 13** ($19.99, Sport Grey L) — was live; confirm Etsy listing status. Repo copy still said “ready not live” until Oct 27. |
| **Etsy Yellow C5** | Still down since July; it was the ad **traffic** leader |
| **Screenshot review** | Intake + scoring rubric: `designs/listings/COPY_CANDIDATES.md`; file drop: `designs/research/screenshots/` |
| **Season** | Late Oct = Q4 gift window opening; car-guy gift tees are a gift-season category, so new listings should go up now, not in December |
| **Printify dashboard (owner screenshot, Oct 27)** | Balance **$0.00** · Orders requiring action **0** · Products published **27** · **Costs to-date $803.09** |

### Real numbers (owner screenshots, Oct 27) — these replace the stale Jun 26 snapshot

**Shop stats, Sep 28 – Oct 27 (30d):**

| Metric | Now | Jun 28 snapshot | Change |
|--------|-----|-----------------|--------|
| Visits | **231** | 455 | **−49%** |
| Orders | **3** | 16 | **−81%** |
| Conversion | **1.3%** | 3.5% | **−63%** |
| Revenue | **$164.62** | $459.10 | **−64%** |

Favorites 13 · shop follows 1 (10 total) · reviews 1 (5★) · **repeat buyers 0** · cities reached 3 ·
**abandoned carts 4**. AOV is **$54.87** (3 orders / $164.62), so orders are multi-item.
Revenue spikes on the graph land ~**Oct 12** and ~**Oct 19–20**, so the last sale was about a week
before this snapshot — not months.

**Etsy Ads, Sep 27 – Oct 27 (30d):** Views **7,054** · Clicks **112** · Orders **1** · Revenue
**$96.25** · Spend **$49.28** · **ROAS 1.95** · views **+204%** vs prior period.
Derived: CTR **1.59%**, click→order **0.89%**.

**Offsite Ads, Sep 27 – Oct 27:** total revenue **$183.16** · direct revenue $71.36 (1 order, 1 new
buyer) · indirect revenue $111.80 (1 order) · **ad fees paid $10.70** (≈5.8% effective). 58 clicks,
**Google 94.83%** (55 visits), Etsy Publishing Partners 5.17% (3). **Leave offsite ads on** — this is
the cheapest traffic in the account.

**Traffic mix problem:** 112 Etsy-ad clicks + 58 offsite clicks ≈ **170 of 231 visits are paid**.
Roughly **60 organic visits/month**. (Attribution windows differ between the two reports, so treat as
directional.) The shop is renting nearly all of its traffic and has almost no organic search footing.

### TRUE P&L (owner screenshots, Oct 27) — Etsy's "net profit" excludes Printify

**Etsy Activity summary, last 12 months (Oct 2025 – Sep 2026):** Etsy-reported **net profit $540.21**

| Line | Amount |
|------|--------|
| Sales (26 total sales, 1 refund −$30.32, buyer duties/tax −$66.31) | **$890.81** |
| Fees (listing −$27.40, transaction −$59.89, processing −$36.11, setup −$29.00, credits +$37.53) | **−$114.87** |
| Marketing (**Etsy Ads −$226.94**, Offsite −$13.34, credits +$4.55) | **−$235.73** |
| Shipping labels | $0.00 |
| **Etsy net profit** | **$540.21** |

**Etsy Activity summary, Oct 2026 month-to-date:** sales $208.29 · fees −$43.00 · marketing −$59.19 ·
**net profit $106.10**. Total balance **−$7.02** (we owe Etsy).

**Printify costs to-date — TWO separate stores:**

| Printify store | Costs to-date |
|----------------|---------------|
| Etsy (`CozyOrbitPrints`) | **$803.09** |
| eBay (`sea-6469`) | **$205.31** |
| **Total production cost, lifetime** | **$1,008.40** |

Tooltip confirms this is total GMV of all Printify order costs for that store to date.

#### The actual bottom line

Etsy's "net profit" is **sales minus Etsy's own fees and ads**. It has never included cost of goods.
Printify production + shipping is our single largest expense and Etsy never sees it.

**Etsy side — this half is clean:**

| | Amount |
|---|--------|
| Etsy net profit, 12mo (Oct 2025 – Sep 2026) | +$540.21 |
| Etsy net profit, Oct 2026 MTD (separate window, no overlap) | +$106.10 |
| Printify, Etsy store | −$803.09 |
| **Etsy all-in** | **−$156.78** |

**eBay side — reconciled Oct 27 (owner order screenshots):**

| Metric | Value |
|--------|-------|
| Orders (hub) | **8** |
| Active listings | 29 |
| 90-day buyer-paid total | **$273.58** |
| Printify store `sea-6469` costs to-date | **$205.31** |

**The 8 orders split two ways — do not mix them in apparel math:**

| Type | Count | Notes |
|------|-------|-------|
| **Printify apparel** | **6** | All Corvette C7/C5 or Dinking Problem pickleball |
| **LEGO resale** | **2** | Oct 4 Star Wars microfighters $30 · Oct 15 City outdoor pack $46 — **no Printify** |

**Six apparel orders (Aug 13 – Oct 25, 2026)** — now in `sales_log.csv`:

| Date | Item | Subtotal | Promoted? |
|------|------|----------|-----------|
| Aug 13 | Dinking Problem tee | $19.99 | no |
| Aug 20 | C7 Illustration tee | $16.47 | yes |
| Sep 13 | Red C7 tee | $16.47 | yes |
| Sep 22 | C7 Sports Car tee | $16.47 | yes |
| Oct 12 | C7 Illustration tee (2nd sale) | $19.99 | yes |
| Oct 25 | Yellow C5 2-sided hoodie | $49.99 | yes |

**Plus four earlier apparel orders already in the log (Jun–Jul):** C5 tee (Michael) · Yellow C5 tee +
hoodie (Allyn, **1st** hoodie on item `398084925179`) · IT WAS IN pickleball.

→ **~10 Printify fulfillments** on the eBay Printify store vs **$205.31** ≈ **$20.50/order average** —
the earlier “unaccounted $120” flag is **resolved** once the Aug–Oct orders are counted.

**LEGO ($76 item + buyer shipping)** rides the same eBay account but is **not** CozyOrbit apparel. It
inflates the 90-day **$273.58** headline — apparel-only buyer subtotals in the 8-order set are **~$215**
items + shipping, and **~$166** if you count only the 6 POD lines’ buyer totals in that screenshot set.

**Apparel takeaway:** eBay is **working for Corvette + type-first pickleball** — five C7 sales via
Promoted Listings, a **second** C5 hoodie at $49.99, and **Dinking Problem already sold Aug 13** (it
was live on eBay; listing copy in repo was behind). C7 tees at **$16.47 promoted** are thin margin;
hoodie at $49.99 is the right AOV play.

**eBay apparel P&L (still approximate):** need **eBay Payments “total earnings”** to finish. Rough
direction: ~$264 apparel item subtotals (10 orders) − $205 Printify − ~13% eBay fees − promoted fees
on most C7 lines → **small positive to breakeven on apparel**, unlike Etsy where ads dominate. LEGO
profit/loss is separate COGS.

**Combined apparel business (Etsy + eBay POD, excluding LEGO):**

| | Amount |
|---|--------|
| Etsy all-in (above) | **−$156.78** |
| eBay apparel (Printify $205.31 vs ~$264 gross items, fees TBD) | **≈ breakeven to modest +** |
| **POD channels combined, rough** | **≈ −$100 to −$140** before LEGO, Cursor, OpenAI |

Still **not** the +$540 Etsy dashboard implies. LEGO and any non-POD sales are upside on the side account.

**Resolved open question:** the eBay store tile reads "**0** in the last 7 days," which confirms the
Printify "Products published" tile is a **7-day** metric. So the Etsy store published **27 products in
7 days** — confirming the rapid listing pace. eBay has had **nothing new pushed to it** in that window.

#### Ads are the structural problem

| Window | Sales | Marketing | Ads as % of sales |
|--------|-------|-----------|-------------------|
| 12 months | $890.81 | $235.73 | **26.5%** |
| Oct 2026 MTD | $208.29 | $59.19 | **28.4%** |

Against post-fee revenue ($890.81 − $114.87 = $775.94), ads ate **30.4%**. POD production already runs
roughly 60–70% of a $22–25 tee. Production + ~13% Etsy fees + ~28% ads is **over 100%** — the business
cannot be profitable at this ad ratio regardless of which designs we list.

October will likely land negative too once Printify is subtracted: $106.10 of Etsy net against roughly
$120–145 of production on $208 of sales.

**Current ad run rate is climbing:** the Oct 27 ledger shows an Etsy Ads bill of **−$4.62 for Oct 26
click-throughs alone**, about a **$139/month** pace. July's working figure was $2.50–3/day.

#### Other facts from these screenshots

- **117 active listings · 32 sales · 4.8★ (10 reviews).** That's **0.27 lifetime sales per listing**.
- **Four more listings published Oct 27** (#4603972103, #4603974639, #4603996160, #4604000300) at
  $0.20 each — still adding inventory while the existing 117 average under a third of a sale apiece.
- **Promo codes `CORVETTE10` and `THANKYOUVETTE` are live shop-wide** and attaching to non-Corvette
  items (a Crochet Lover Tee favorite shows `CORVETTE10`). A 10% coupon stacking on top of ~28% ads
  and ~65% production is where the remaining margin goes.
- **`Pickleball Two Neon Eyes` is the most-favorited listing in the shop** — 4 of the 13 favorites
  (Judith, Florante, Renee, meghanpotemra) — with **zero sales ever**. The art attracts and the price
  closes nobody, even with a coupon live. Before killing it outright, one price-drop test is defensible.

### Corvette is still what sells — ads just aren't pointed at it

**Corvette listings are still live** — the Recent activity feed shows a **Corvette C5 Blueprint Poster
purchased ~Oct 22**, a 5★ review on the **Yellow Corvette C6 V8 Hoodie** (Michel, Oct 6), and a **Kids
Play Mat Car Floor Mat purchased Oct 14**. What's missing is Corvette listings *in the advertised set*.

**Of the 3 orders in the last 30 days, at least 2 are car products** (C5 Blueprint Poster ~Oct 22, Kids
Play Mat Oct 14; the third was a 3-item order, contents unknown). Meanwhile the ad budget is aimed
almost entirely elsewhere. The car products are converting **organically, with coupons, unadvertised**,
while ~$49/mo of ads goes to niches that produced one order between them.

The Oct 1–27 ad table lists **~45 advertised listings, every one ads-ON, with no Corvette among them.**
The proven catalog (C4 Minimal ROAS 4.06, C8 ROAS 3.06, Yellow C5, C7 Illustration, C5 Blueprint) is
absent from ads. The advertised set instead spans ~10 unrelated niches:

national parks (Acadia ×2, Zion, Joshua Tree ×2, Yosemite, Glacier, Yellowstone, Smoky Mtns, Turkey
Run, Indiana Dunes, Brown County) · fishing (ice, fly, bass, walleye, trout) · science diagrams
(mitochondria, neuron, opossum, squirrel, engine, turbo, tardigrade) · Christian (3) · crafts
(crochet, quilting) · holidays (Santa, Christmas truck, Merry Teacher, Halloween, Skelly) · Bay Area
(Oakland ×2, San Francisco) · "lamps?" memes (3) · pickleball (2) · misc one-liners.

**This is the actual cause of the dry spell.** Attention and ad budget moved off the only line with
repeat buyers and 5-star reviews and onto ~45 cold listings across ten niches. Repeat buyers is **0**
for the first time. Nothing has depth, so nothing earns organic rank.

### Ad budget is too thin to learn anything

**$49.28 across ~45 listings ≈ $1.09 per listing per month.** At that spend almost every listing got
0–3 clicks, which proves nothing either way. Only two listings have a readable sample:

| Listing | Views | Clicks | CTR | Orders | Spend | ROAS | Read |
|---------|-------|--------|-----|--------|-------|------|------|
| **It Was In pickleball** | 510 | 9 | 1.8% | **1** | **$5.27** | **18.26** | Only winner; starved of budget |
| **Pickleball Two Neon Eyes** | 1,494 | 31 | 2.1% | **0** | **$9.01** | 0 | Biggest spender, **0 sales since Jul 16** |
| Squirrel Diagram Conspiracy | 171 | 6 | **3.5%** | 0 | $3.05 | 0 | Best real CTR — concept clicks; sample too small |
| Smoky Mountains TN | 44 | 3 | 6.8% | 0 | $1.78 | 0 | Tiny sample, note only |
| Engine Diagram | 239 | 3 | 1.3% | 0 | $2.09 | 0 | Car-adjacent bridge back to proven niche |
| Turbo Blueprint "Spool Responsibly" | 221 | 3 | 1.4% | 0 | $2.70 | 0 | Car-adjacent bridge back to proven niche |

**ROAS 1.95 is a loss on POD.** $96.25 revenue − $49.28 ad spend − ~$55-65 Printify − ~$10 Etsy fees
is negative. ROAS needs to clear roughly **3.0** before ads pay for themselves at our cost structure.

### Action list from this snapshot (ordered by dollars)

1. **Cut Etsy Ads hard — this is the whole problem.** At 28% of sales, ads cannot be paid for out of
   POD margins. Target **under 10% of sales**, i.e. roughly **$20/month**, until a listing proves it
   can clear ROAS 3.0. Everything else on this list is secondary to this.
2. **Concentrate what's left.** Cut from ~45 advertised listings to **3–5**. Lead with It Was In
   (ROAS 18.26, currently receiving 11% of spend) plus the car listings that are already converting
   organically. $20 across four listings still buys more readable data than $49 across 45.
3. **Kill ads on the national-parks long tail** (11 listings, mostly 0–1 clicks, 0 orders). Keep them
   listed; just stop paying for them.
4. **`Pickleball Two Neon Eyes`:** most-favorited listing in the shop, 1,494 views, 31 clicks, **0 sales
   in 3 months**, and the biggest ad line item at $9.01/mo. Pull ads now. Optionally run one price-drop
   test organically before delisting, since favorites say the art works and the price doesn't.
5. **Put the Corvette line back in front of buyers.** Two of three October orders were car products,
   unadvertised. C4 Minimal at ROAS 4.06 with repeat organic demand is the highest-confidence revenue
   in the account and is currently earning nothing.
6. **`Halloween Porgs T-Shirt` — IP RISK, pull it.** Porgs are Disney/Lucasfilm (Star Wars). We already
   took one Etsy takedown in July over the Corvette wordmark; a second strike is not worth a 55-view
   listing. Check the **Policy violations** tab while in there.
7. **Stop publishing new listings for now.** 117 active at 32 lifetime sales is **0.27 sales per
   listing**, and four more went up on Oct 27. More inventory is not the constraint.
8. **Reconsider the shop-wide 10% coupons** (`CORVETTE10`, `THANKYOUVETTE`). A coupon on top of 28% ads
   on top of ~65% production is why orders land near zero margin. Keep coupons for abandoned-cart
   recovery, not as an always-on shop-wide discount.
9. **Work the 4 abandoned carts** — at $54.87 AOV those are worth more than a month of ads.
10. **Leave offsite ads on.** $13.34 of fees across 12 months against $183.16 of revenue in the last 30
    days alone is the best ratio in the account.

**Corrections to earlier analysis in this session:**
- The theory that no new listings went up was wrong — the opposite happened (117 active, 4 more on Oct 27).
- "Corvette is gone from the shop" was wrong. Corvette listings are live and still converting; they are
  absent from **ads**, not from the catalog.
- The dry spell is narrower than reported: the last order was **~Oct 22**, about five days before this
  snapshot, not months ago.

**Copy-candidate batch 1 reviewed Oct 27** — 16 screenshots scored in `COPY_CANDIDATES.md`.
Build order: list Dinking Problem (already export-ready) → `WRONG HOLE` pickleball gag → red gothic
chest script front/back → vintage photo-collage Corvette. Four candidates auto-skipped for brand
wordmarks (Busch, Modelo, Benadryl) or licensed characters (Superman shield).

## July 21 update (post IT WAS IN sale)

| Item | Status |
|------|--------|
| **eBay Pickleball IT WAS IN** | **SOLD Jul 17 — $18.99** + $3.99 ship; mint; Printify **#27858258.4** ready-to-ship **$14.63**; eBay fees **$3.53** → earnings **$19.45** → **~$4.82 cash** |
| **Pickleball Soft Serve / Eyes Up Here** | Still **0 sales** (only type+ball gag converted) |
| **Dinking Problem** | **READY** — `designs/pickleball/pickleball_dinking_problem_UPLOAD_TO_PRINTIFY.png` + `PICKLEBALL_DINKING_PROBLEM.md` — upload next |
| **Wave 2 briefs** | `PICKLEBALL_WAVE2.md` — Kitchen / Six pack after Dinking live |
| **Margin rule** | Next pickleball tees **$20.99+** S–XL — $18.99 is thin |
| **Ads** | Keep pickleball promoted **light**; Yellow C5 Ad Fee lesson still applies |
| **Do not build tonight** | Comic-panel memory shirt; Lincoln portrait; doodle club; goose grid |

## July 16 Mac catch-up

| Item | Status |
|------|--------|
| **eBay Yellow C5 tee** | Sold **$26.09** + $3.99 ship; buyer total $31.28; **earnings $21.68** after tax + $4.65 txn + **$3.75 Ad Fee General** |
| **Printify tee** | List **$21.71** → paid **$11.71** with **$10 coupon** (prod $9.15 + ship $2.56) → **~$9.97 cash profit**; without coupon ≈ **−$0.03** (owner was right) |
| **eBay Yellow C5 hoodie 2-sided** | Sold **$51.99**; **Printify not synced yet** — check morning |
| **Etsy Yellow C5** | **Taken down** (IP risk — design shows **CORVETTE** wordmark). Do not relist same art on Etsy. |
| **eBay channel** | Re-prioritize — now **4 shirt/hoodie sales** including pickleball. Promoted fees are eating tee margin. |
| **Pickleball Soft Serve tee** | **LIVE** Jul 16 — Etsy + eBay; Gildan; $19.99–$23.99 (3XL); original ice cream cone art |
| **Pickleball Eyes Up Here tee** | **LIVE** Jul 16 — Etsy + eBay; arrow + two balls; transparent holes; dark shirts |
| **Pickleball IT WAS IN tee** | **LIVE** Jul 16 — Etsy + eBay; **first sale Jul 17 $18.99** (mint); dark shirts |

**Structural fix for Yellow C5 tee on eBay:** raise item price and/or cut Ad Fee % — $3.75 ad on a $26 item is why it only breaks even without coupons.

### Pickleball Soft Serve (Jul 16 night — LIVE)

| Channel | URL | Notes |
|---------|-----|-------|
| **Etsy** | https://www.etsy.com/listing/4538686602/soft-serve-ice-cream-character-tee-cute | Listing ID `4538686602`; shop section = keep separate from Corvette hero |
| **eBay** | https://www.ebay.com/itm/398179685959 | Item `398179685959`; S–XL **$19.99**, 2XL **$21.99**, 3XL **$22.99**; Printify shows ~$10 prod profit before marketplace fees |
| **Print file** | `designs/pickleball/pickleball_soft_serve_UPLOAD_TO_PRINTIFY.png` | Original cone character — not TikTok pickle clone |
| **Ads rule** | Light promoted or off for first 48–72h | Do not stack sale + heavy Ad Fee (Yellow C5 lesson) |

### Pickleball Eyes Up Here (Jul 16 — LIVE)

| Channel | URL | Notes |
|---------|-----|-------|
| **Etsy** | https://www.etsy.com/listing/4538870176/funny-pickleball-balls-t-shirt-two-neon | Listing ID `4538870176` |
| **eBay** | https://www.ebay.com/itm/398181098143 | Item `398181098143` |
| **Print file** | `designs/pickleball/pickleball_eyes_up_here_UPLOAD_TO_PRINTIFY.png` | Arrow + two balls; transparent holes; dark shirts |

### Pickleball IT WAS IN (Jul 16 — LIVE · sold Jul 17)

| Channel | URL | Notes |
|---------|-----|-------|
| **Etsy** | https://www.etsy.com/listing/4538866895/it-was-in-pickleball-ball-t-shirt | Listing ID `4538866895` |
| **eBay** | https://www.ebay.com/itm/398181038019 | Item `398181038019` · **sold Jul 17 $18.99** mint |
| **Print file** | `designs/pickleball/pickleball_it_was_in_UPLOAD_TO_PRINTIFY.png` | Minimal line-call; dark shirts |
| **P&L** | ~$4.82 cash | fees $3.53 · Printify $14.63 · raise next SKUs to $20.99+ |

### Pickleball Dinking Problem (LIVE on eBay · sold Aug 13, 2026)

| Channel | URL | Notes |
|---------|-----|-------|
| **eBay** | item **398222322676** | **Sold Aug 13** $19.99 Sport Grey L (V. Protti); delivered |
| **Etsy** | confirm in Listings | Repo had “not live” through Jul — verify Etsy status |
| **Print file** | `designs/pickleball/pickleball_dinking_problem_UPLOAD_TO_PRINTIFY.png` | Type-first white/lime/white; ball below; dark shirts |
| **Listing** | `designs/listings/PICKLEBALL_DINKING_PROBLEM.md` | eBay S–XL **$20.99** |
| **Compose** | `scripts/compose_pickleball_dinking_problem.py` | No OpenAI |

---

## July 3 weekend snapshot (from mobile session — source: `COZY_ORBIT_HANDOFF.md`)

| Item | Status |
|------|--------|
| **July 4th sale** | 10% off, **26 listings**, ends Sunday midnight |
| **Thumbnails** | Swapped most listings to **clean mockup photos** (done Jul 3) |
| **Month 1 P&L (approx)** | ~19 sales · ~$552 Etsy net · ~$457 Printify · ~$118 ads → **~-$90 to -$140** all-in |
| **Design pivot** | Stop full AI shirt gen; double down on **Blueprint** + gothic **variants only** |
| **Next listing** | **C6 Blueprint** (front/back, same system as C5 Blueprint winner) |

### Etsy Ads (Jul 3 — overrides Jun 26 snapshot below)

- Budget cap **$10/day**; actual spend ~**$2.50–3/day**
- **ON:** C5 Blueprint (added Jul 3), C8 (ROAS 2.61), C4 (2.23), C7 (1.85), Yellow C5 (1.76)
- **OFF / pause:** Supra, C7 V8 Sports, any C5 ad listing with $0 revenue
- Last 30 days: **$130 spend · $238 revenue · ROAS 1.83 · 7 orders**
- July spend to date: under ~$7 (intentional cut after Jul 1 pause pass)

**Weekend rule:** no more shop tweaks after tonight — check Monday stats.

---

## Strategy (current)

| Track | Status |
|-------|--------|
| **Old designs** | Proven sellers — keep live; keep ads running for now while collecting more data |
| **Variant B (debadged)** | Copyright-safer test — C5 live @ ~$21; **C6 B blocked — regen with no-plate prompt when OpenAI credits return** (Pillow fix abandoned) |
| **C8 line-art** | Listed but low CTR; art not strong enough to push ads yet |
| **eBay cross-listing** | Lower-fee volume channel — first eBay shirt sale hit C5 old art; promoted general listings can stay aggressive if net profit stays **$5+** |

**Near-term research:** next design for Etsy + eBay should build on proven Corvette/C4/C5 demand before jumping to unrelated niches.

### Next design research direction (2026-06-18 late)

**Recommendation:** make a **C4 pop-up headlights / 90s wedge** design next. C4 Minimal now has repeat Etsy demand, and marketplace checks show C4-specific hooks with visible demand: ZR-1, pop-up headlights, fourth-gen silhouette, 1984–1996 nostalgia, and red/black/silver car variants.

**Design brief:** front or front-3/4 C4 with pop-up headlights up, no badges/logos, crisp 90s motorsport poster feel, light-shirt-safe palette, optional text like “POP-UP ERA” / “FOURTH GEN” instead of trademark-heavy wording. Cross-list to eBay with aggressive pricing after Etsy listing is live.

**Generated master:** `designs/corvette/c4_popup_collection_master.png` — QC pass: matches C5/C6/C7 collection system, huge distressed `C4`, clean red C4-style wedge, raised pop-up headlights, `V8` bottom-left, correctly spelled quote, no obvious Corvette/crossed-flag wordmarks.

**Printify upload:** `designs/corvette/c4_popup_collection_master_UPLOAD_TO_PRINTIFY.png` — exported with `--threshold 235`, size 3951×4919, transparent background. Needs listing copy before upload/listing.

**New controlled variant (Jun 27 evening):** `designs/corvette/c4_popup_gothic_collection.png` + `designs/corvette/c4_popup_gothic_collection_UPLOAD_TO_PRINTIFY.png` — black C4-style wedge, raised pop-up headlights, chrome/silver wheels, local readable typography (`POP-UP ERA`, `FOURTH GEN V8`, `1984-1996`), no visible logos/wordmarks/plate. Preview checked on White, Natural, Sport Grey, and Light Blue. Listing: `designs/listings/C4_POPUP_GOTHIC.md`. **Uploaded to Etsy Jun 27** at **S-XL $23.99**, **2XL $26.99**, **$4.75 shipping**; offsite ads ON at **15%**; owner-calculated floor profit **at least $6.62/shirt** after fees + production.

**Do not use:** `/Users/ostynseabolt/.cursor/projects/Users-ostynseabolt-ai/assets/c4_popup_era_master.png` — good standalone concept but off-system versus the Corvette collection style.

### C3 Stingray collection candidate (2026-06-19 early)

**Generated master:** `designs/corvette/c3_stingray_collection_master.png` — QC pass: matches collection system, huge distressed `C3`, silver shark-body C3-style coupe, `V8` bottom-left, correctly spelled quote, no obvious Corvette/crossed-flag wordmarks.

**Printify upload:** `designs/corvette/c3_stingray_collection_master_UPLOAD_TO_PRINTIFY.png` — exported with `--threshold 235`, size 3951×4919, transparent background. Needs listing copy before upload/listing.

### C5 Z06 / fixed-roof coupe candidate (2026-06-19 early)

**Generated master:** `designs/corvette/c5_z06_collection_master_ls6.png` — QC pass: matches collection system, huge distressed `C5`, blue fixed-roof/Z06-style C5 coupe, `V8` bottom-left, stronger quote correctly spelled: “Light. Stiff. LS6. Built before comfort got in the way.” No obvious Corvette/crossed-flag/Z06 wordmarks.

**Printify upload:** `designs/corvette/c5_z06_collection_master_ls6_UPLOAD_TO_PRINTIFY.png` — exported with `--threshold 235`, size 3951×4919, transparent background. Needs listing copy before upload/listing.

**Do not use:** `designs/corvette/c5_z06_collection_master.png` — good car/layout but weaker generic quote.

**Next candidates:** C6 Z06 / track style; C2 split-window collection; Porsche 911 / Mustang / JDM only after Corvette winners get more variants because those niches are more crowded and less proven for this shop.

**C6 Z06 color note:** common C6 Z06 colors include Black, Victory Red / Torch Red, Velocity Yellow, Machine Silver, and Cyber Gray. For C5 Z06, Torch Red and Black are the safest/commonest colors.

### C6 Z06 Velocity Yellow candidate (2026-06-19 early)

**Generated master:** `designs/corvette/c6_z06_velocity_yellow_collection_master.png` — QC pass: matches collection system, huge distressed `C6`, Velocity Yellow C6 Z06-style coupe, visible hood scoop, side vent, wide stance, black wheels, `V8` bottom-left, quote correctly spelled: “7.0 liters. 505 horses. Built wide. Born wild.” No obvious Corvette/crossed-flag/Z06 wordmarks.

**Printify upload:** `designs/corvette/c6_z06_velocity_yellow_collection_master_UPLOAD_TO_PRINTIFY.png` — exported with `--threshold 235`, size 3951×4919, transparent background. Needs listing copy before upload/listing.

**Tycoon HQ (local):** `visualizations/cozy_orbit_tycoon.html`  
- Rebuild once: `.venv/bin/python scripts/build_tycoon_hq.py`  
- Stay live: `.venv/bin/python scripts/build_tycoon_hq.py --serve` → http://127.0.0.1:8765/cozy_orbit_tycoon.html  
- Also refreshes when you run `shop_daily_brief.py`  
**Later:** consolidate C5 listings after variant B has data · orange color variants (Velocity Yellow C6, etc.)

---

## Etsy shop branding (2026-06-14)

| Asset | File | Size | Status |
|-------|------|------|--------|
| Profile icon | `designs/corvette/cozy_orbit_etsy_profile_500.png` | 500×500 | **Uploaded** (solo yellow C5 hero) |
| Shop banner | `designs/corvette/cozy_orbit_etsy_banner_3360x840.png` | 3360×840 | **Uploaded** |

**Regenerate profile hero (OpenAI):** `.venv/bin/python scripts/generate_banner_cars.py --profile --force`  
**Regenerate profile composite:** `.venv/bin/python scripts/build_etsy_shop_assets.py --profile-only`  
**Regenerate banner:** `.venv/bin/python scripts/build_etsy_shop_assets.py --banner-only`  
**Generate banner cars (OpenAI, transparent PNGs):** `.venv/bin/python scripts/generate_banner_cars.py`  
**Profile source:** `designs/corvette/banner/etsy_profile_c5_hero.png`  
**Banner source assets:** `designs/corvette/banner/etsy_banner_c5_yellow.png`, `etsy_banner_c6_white.png`, `etsy_banner_c7_black.png`  
**Profile:** solo debadged yellow C5 on charcoal — no text · **Banner:** C5 / C6 / C7 lineup + tagline

### Upload checklist (Etsy → Shop Manager → Settings)

- [x] **Icon:** Upload `cozy_orbit_etsy_profile_500.png` (Shop icon / profile picture)
- [x] **Banner:** Upload `cozy_orbit_etsy_banner_3360x840.png` (Cover photo / banner)
- [ ] Confirm icon matches banner at thumbnail size (~48px)
- [ ] Confirm no Chevrolet crossed flags / Corvette wordmarks visible in crops

---

## Sales summary (user-reported; Jul 16 = 17+ Etsy + 3 eBay units logged)

| Date | Buyer | Listing | Qty | Color | Size | Notes |
|------|-------|---------|-----|-------|------|-------|
| Jun 2 | Seth | C5 Illustrated **front/back** | 1 | Ash | M | **1st sale, pre-ads organic**; ~breakeven ($20.99 item, Printify $22.92) |
| Jun 3 | David | C6 **old design** | 1 | Gold | 2XL | 5★ review; **repeat customer** (returned Jun 25) |
| Jun 6 | Tavian | C6 **old design** | 1 | White | M | Delivered |
| Jun 11 | mark | Yellow C5 | 1 | Light Blue | L | Etsy Ads; no complaints |
| Jun 12 | Patrick | C7 Illustration | **2** | White | L | 1 order, 2 shirts; Switzerland |
| Jun 14 | Suzanne | C4 Minimal | 1 | Sport Grey | 2XL | Best ad ROAS |
| ~Jun 15 | — | **C8 Tee** | **2** | — | — | Etsy Ads; ~$50 revenue; 2 shirts in 1 order |
| Jun 18 | — | **Kids Play Mat** (Town Road) | **2** | Front mat | — | **Organic** (no ads); $70 order total; 20% abandoned-cart coupon; Printify ~$65 → ~breakeven |
| Jun 18 | Chris | **C4 Minimal** | 1 | Red | XL | Etsy sale; Printify $19.54; est. profit ~$6.92 after Etsy fees |
| Jun 18 | Michael | **C5 Illustrated** | 1 | Heather Clay | 2XL | **First eBay shirt sale**; Printify $18.57; est. profit ~$9.46 before any separate promoted fee |
| Jun 25 | David L Ghirardi | **Z06 Yellow C6 V8 Race Car Tee** | 1 | Sport Grey | 2XL | Coupon `CORVETTESUMMER` (15% off); repeat customer |
| Jun 25 | David Vilella | **C6 old design** | 1 | White | L | Coupon `CORVETTESUMMER` (15% off) |
| Jun 26 | Patricia Sharman | **C7 classic graphic tee** | 1 | Sport Grey | 2XL | Coupon `CORVETTESUMMER` (15% off) |
| Jun 26 | Lona Mickelson | **Yellow C5** | 1 | White | L | Coupon `CORVETTESUMMER` (15% off); latest reported sale |
| Jun 27 | — | **Organic Etsy order** (listing details pending) | 1 | — | — | User morning report: non-ad-attributed sale |
| Jun 27 | — | **C5 + C7** (same Etsy Ads order) | **2** | — | — | User morning report: ad-attributed order with 2 shirts |
| Jun 28 | michel salaun | **C4 Minimal** | 1 | Light Blue | 2XL | France order; order `4102687761`; coupon `VETTESUMMER` (10% off); overnight sale after price-floor changes |
| Jun 30 | sydney roberts | **C5 Blueprint** front/back | 1 | Black | XL | Gift order; order `4104565447`; Oklahoma City OK; Printify $26.49; est. profit ~$5.08 |
| Jul 15 | Allyn Davis | **Yellow C5** tee (eBay) | 1 | White | — | **Repeat buyer**; Cortland NY; ~$9.97 w/ Printify coupon |
| Jul 15 | Allyn Davis | **Yellow C5** hoodie 2-sided (eBay) | 1 | Ash | 2XL | **$50.58 earnings**; item `398084925179`; ship by Jul 29; Printify pending |
| Jul 16 | — | **Pickleball Soft Serve** (listed) | — | — | — | Etsy + eBay live; still 0 sales as of Jul 21 |
| Jul 17 | — | **Pickleball IT WAS IN** (eBay) | 1 | Mint | — | **First pickleball sale** $18.99 → ~$4.82 cash; Soft Serve + Eyes still 0 |

**Refunded:** Jan — C5 Illustration Vintage — accidental order.

**Reconciliation note (Jun 26):** user-confirmed totals are **15 sales** (**14 Etsy, 1 eBay**). Etsy orders panel snapshot was **13** orders because it lagged by ~5 hours; one additional Etsy sale landed afterward.

**Morning update (Jun 27):** user reported **2 additional Etsy orders** this morning (**3 units total**), including one organic order and one Etsy Ads order containing **C5 + C7** shirts. Revenue callout from user: approximately **$431** in Etsy revenue after nearly one month.

**Afternoon update (Jun 28):** overnight Etsy sale on **C4 Minimal** (Light Blue / 2XL) to France after repricing floor lift. Etsy stats screenshot showed **455 visits · 16 orders · 3.5% conversion · $459.10 revenue** YTD snapshot at time of capture.

### Pricing floor policy (Jun 28)

- Shop repricing pass completed: most shirts now at **$21.99+** minimum.
- Current lowest shirt is **Kids C5** at **$20.99**; next lowest tier is **$21.99**.
- Working rule: hold new prices stable for **48-72h** before another global price change to preserve clean conversion read.

### C5 Blueprint front/back pricing (Jul 1)

- **S–XL:** $32.99 (Printify prod ~$21.74 → ~$7.21 before Etsy fees)
- **2XL:** $35.99 (prod ~$24.31)
- **3XL:** $37.99 (prod ~$26.32)
- **Real profit after Etsy fees:** ~$5–6 organic, ~$3–4 if ad-attributed — hold stable 1 week before next change.
- **Do not add to ads** until 2+ organic sales at new price.

### P&L reconciliation (owner screenshots)

**June 2026 close (Jul 1 morning):**
- Etsy activity summary (June): **net profit $386.37** (after Etsy fees + $127.93 ads; 18 items, 1 refund).
- Printify June charges (13 fulfilled orders, 1 canceled): **~$344.31** total production+ship.
- **Cash net after Printify only:** `386.37 - 344.31 = +$42.06` before eBay/Cursor/OpenAI/other expenses.
- eBay first payout received **$17.20** (Jun 18 C5 sale; est. shirt profit ~$9.46 before any promoted fee).
- First Etsy payout received **$18.51** (partial; more June balance still pending/on hold).
- **Realistic June all-in:** roughly **breakeven to ~$50 profit** once eBay is included and Cursor/subscription costs are subtracted — not a loss month at close, but thin margins while ads ramped.
- Tavian return was handled privately (USPS + Venmo reimbursement per owner notes); keep as separate cash adjustment.

**Prior snapshot (Jun 26 evening, superseded):** Etsy net $278.77 vs Printify $349.12 showed operational loss before late-month sales landed.

### Reviews snapshot (Jun 26)

- Current known reviews: **3 total, all 5-star** (Tavian, David, Patrick).
- Positive buyer support/response quality is explicitly mentioned in Tavian review text.

---

## Listing ↔ file mapping

### Live / selling (old art)

| Etsy listing (approx) | Design file | Notes |
|------------------------|-------------|-------|
| C5 Illustrated front/back (~$25.58+) | `corvette_c5_streetwear_design` + back | **First sale horse** (Seth) |
| C6 Sports Car Tee | `corvette_c6_streetwear_design` (old) | 2 sales; **do not replace** until variant B tested |
| C7 Car Illustration | `corvette_c7_streetwear_design` | Patrick 2× |
| C4 Minimal Logo | `corvette_c4_minimal_front` | Best ROAS; repeat Etsy seller |
| Yellow C5 | `corvette_c5_yellow_streetwear_design` | Ad traffic leader |

### Test / new (copyright-safer)

| Listing | Master | Printify export |
|---------|--------|-----------------|
| C5 Variant B (~$21) | `c5_variant_B_blackwheels_plate.png` | `c5_variant_B_blackwheels_plate_UPLOAD_TO_PRINTIFY.png` |
| C6 Variant B (**blocked — regen**) | `c6_variant_B_collection.png` | `c6_variant_B_collection_UPLOAD_TO_PRINTIFY.png` — do not list until regen |
| C7 Variant B | `c7_variant_B_collection.png` | `c7_variant_B_collection_UPLOAD_TO_PRINTIFY.png` |
| **C7 Torch Red** (color variant) | `c7_torch_red_collection.png` | `c7_torch_red_collection_UPLOAD_TO_PRINTIFY.png` |
| **C5 Torch Red** (color variant) | `c5_torch_red_collection.png` | `c5_torch_red_collection_UPLOAD_TO_PRINTIFY.png` |
| **C7 Laguna Blue** (color variant) | `c7_laguna_blue_collection.png` | `c7_laguna_blue_collection_UPLOAD_TO_PRINTIFY.png` |
| **C7 Velocity Yellow** (color variant) | `c7_velocity_yellow_collection.png` | `c7_velocity_yellow_collection_UPLOAD_TO_PRINTIFY.png` |
| **C6 Atomic Orange** (color variant) | `c6_atomic_orange_collection.png` | `c6_atomic_orange_collection_UPLOAD_TO_PRINTIFY.png` |
| **C5 Black** (color variant) | `c5_black_collection.png` | `c5_black_collection_UPLOAD_TO_PRINTIFY.png` |
| **C8 Black Gothic** (color/style variant) | `c8_black_gothic_collection.png` | `c8_black_gothic_collection_UPLOAD_TO_PRINTIFY.png` |
| **C4 Pop-Up Gothic** | `c4_popup_gothic_collection.png` | `c4_popup_gothic_collection_UPLOAD_TO_PRINTIFY.png` |

**C7 Laguna Blue (2026-06-14):** Debadged nose, front splitter, solid V8. Export **`--threshold 235`**. **Light shirts only.** Listing: `designs/listings/C7_LAGUNA_BLUE.md`.

**C7 Velocity Yellow (2026-06-15):** Debadged, solid V8. Option E quote via overlay (`--preset velocity-yellow`). Export **`--threshold 235`**. **Light shirts only.**

**C6 Atomic Orange (2026-06-15):** Debadged, no plate, solid V8. Default razor-sharp quote overlay. Export **`--threshold 235`**. **Light shirts only.** Price **$24.99–$27.99**.

**C5 Torch Red (2026-06-14):** v3 — debadged nose, front splitter lip, solid V8. Export **`--threshold 235`**. **Light shirts only.** Listing: `designs/listings/C5_TORCH_RED.md`. v1 backup: `backups/c5_torch_red_v1_badge_slop.png`.

**C5 Black (2026-06-15):** Debadged, chrome/silver wheels (contrast on white), solid V8. C5 quote via overlay (`--gen c5`). Export **`--threshold 235`**. **Light shirts only** — black car vanishes on dark colors. Listing: `designs/listings/C5_BLACK.md`. Script: `scripts/generate_c5_black.py`.

**C7 Torch Red (2026-06-14):** Color variant — factory Torch Red, crossed-flags nose badge, solid V8. Export **`--threshold 235`**. **Light shirts only:** White, Natural, Sport Grey. Listing: `designs/listings/C7_TORCH_RED.md`. v1 backup: `backups/c7_torch_red_v1_cream_bg.png`.

**C7 variant B (2026-06-18):** Regenerated clean using Cursor image gen after OpenAI hard billing limit blocked `generate_c7_variant.py`. Final master has **no AI small text**; quote added locally in solid black. **Do NOT run `overlay_collection_quote.py`** on this black-car master. If regenerating later: car/C7/V8 only → add quote with `solidify_c7_variant_quote.py` → export with `--threshold 245`. Listed on **Etsy** and cross-listed to **eBay**. Etsy pricing: most sizes **$23**, 2XL **$24**, Etsy Ads **15%**. eBay pricing: sale/promoted pricing around **$16+** because fees are cheaper and profit still clears **$5+/shirt**. Listing: `designs/listings/C7_VARIANT_B.md`.

### Listed but weak

| Listing | File | Issue |
|---------|------|-------|
| C8 Tee | `corvette_c8_UPLOAD_TO_PRINTIFY.png` | Correct mid-engine; line-art style user wouldn't wear; lifestyle hero hurts CTR — use model front white |

### Do not list

| File | Reason |
|------|--------|
| `c8_variant_B_collection.png` | Wrong generation (C7 body) |
| `corvette_c8_streetwear_design` (old) | Front-engine, not C8 |

---

## Etsy Ads snapshot (2026-06-26, last 30 days) — **SUPERSEDED by the Oct 27 block at the top**

| Listing | Views | ROAS | Ad orders |
|---------|-------|------|-----------|
| Corvette C4 Minimal | 1,139 | 4.06 | 2 |
| Corvette C8 Tee | 2,010 | 3.06 | 1 |
| Yellow Corvette C5 | 1,611 | 2.23 | 1 |
| Corvette C7 Illustration | 3,438 | 1.05 | 1 |
| C6 old | 1,007 | 0 | 0 |
| Yellow C5 hoodie | 80 | 0 | 0 |
| Red C4 pop-up tee | 79 | 0 | 0 |
| Yellow C6 hoodie | 42 | 0 | 0 |
| C7 V8 hoodie | 34 | 0 | 0 |

**Current pain:** most spend still concentrated in top 4 listings; long tail remains mostly no-order.  
**Account (30d):** 12.4K views · 163 clicks · 6 ad orders · $195.51 revenue · $100.96 spend · **ROAS 1.94**.  
**Budget rule now:** with a $10/day cap, keep spend concentrated on winners (C4 Minimal, Yellow C5, C8 Tee); keep C7 Illustration on a short leash; keep C6 old low-exposure only.
**Owner note (Jun 27):** ad budget remains **$10/day**, but Etsy is typically spending around **$7/day or less**; treat this as inventory/opportunity-limited delivery, not overspend.

**Detailed listing metrics from Etsy Ads table:**  
- C4 Minimal: 21 clicks, 1.8% CTR, $55.89 rev on $13.76 spend  
- C8 Tee: 19 clicks, 0.9% CTR, $50.00 rev on $16.36 spend  
- Yellow C5: 25 clicks, 1.6% CTR, $27.49 rev on $12.31 spend  
- C7 Illustration: 52 clicks, 1.5% CTR, $39.18 rev on $37.28 spend

**Ads ON (Jul 3 — current):** C5 Blueprint, C8 Tee, C4 Minimal, C7 Illustration, Yellow C5.
**Ads OFF / remove if still on:** Supra MK4, C7 V8 Sports/hoodie, C5 Blueprint Poster, any C5 ad listing with $0 revenue.
**Ads OFF (Jul 1 pass, keep off):** C6 old, Yellow C5 hoodie, Red C4 pop-up, Red C8, Yellow C6 hoodie, C4 Engine, C8 Night Run.
**Do not** add new random listings to ads this weekend — let sale + thumbnail changes bake until Monday.

### Live intervention (2026-06-24 midday)

- **Sale launched:** Etsy shop-wide/listing-targeted promo at **15% off for 48 hours** (started today).
- **Ad tightening applied:** most listings paused; ads kept ON for listings with **CTR > 1.5%**, listings with prior sales, and newly added sweatshirts (last ~4 days) that have minimal/no spend yet.
- **Current ad footprint:** **$10/day across 9 listings**; bottom 4 ad slots are fresh tests created ~4 days ago (including sweatshirt tests).
- **2026-06-26 check:** ads still set to **$10/day**.
- **Intent:** force limited daily budget into either proven converters or fresh low-spend tests while favorites/abandoned-cart traffic is high.
- **Readout window:** evaluate after 48 hours using orders, spend per order, and cart/favorite movement before re-expanding any paused listings.
- **Guardrail:** if a sweatshirt still shows 0 clicks after meaningful impressions, pause and reallocate back to proven tee winners.

## eBay snapshot (updated 2026-10-27)

- **Hub:** 29 active · **8 orders total** · 4 unsold · **90-day sales $273.58** (includes **2 LEGO** resale lines).
- **Printify store `sea-6469`:** costs to-date **$205.31** · **0 products published in last 7 days** (contrast: Etsy pushed 27 in 7d).
- **Apparel (~10 Printify orders lifetime):** Jun C5 tee · Jul Yellow C5 tee + hoodie (#398084925179, **sold again Oct 25** $49.99 Light Blue L) · Jul IT WAS IN · Aug **Dinking Problem** · Aug–Oct **five C7/C7-variant tees** (mostly **Promoted Listings** at $16.47–19.99).
- **Not apparel:** LEGO Star Wars microfighters (Oct 4) · LEGO City outdoor pack (Oct 15) — track separately from CozyOrbit POD P&L.
- **Channel read:** eBay converts **Corvette + type-first pickleball** when promoted; **$16.47 C7 tees are volume plays** — watch promoted fee % so net stays **$5+**. Hoodie **$49.99** is the margin anchor.
- **IP note:** Yellow C5 art still has **CORVETTE** wordmark — Etsy down; eBay still selling (2 hoodie sales). Plan safer replacement before scaling ads.

## Weekend promo test (2026-06-19 late)

- **Offer launched:** 2 C7 designs bundled at **15% off** (weekend test).
- **Intent:** raise AOV and convert warm traffic without changing Etsy ad allocation.
- **Hold constant through weekend:** keep ad toggles as-is to preserve clean test data.
- **Monday readout:** compare orders, units/order, and net profit/order before deciding whether to expand this offer to C4/C5 winners.

**Daily brief:** `cd ~/ai && .venv/bin/python scripts/shop_daily_brief.py`

---

## Shirt colors

- **Pickleball Dinking Problem / Eyes / IT WAS IN:** Black, Navy, Charcoal (dark only — white/lime type)
- **C7 Laguna Blue:** White, Natural, Sport Grey only (not dark colors)
- **C5 Torch Red:** White, Natural, Sport Grey only (not dark colors)
- **C5 Black:** White, Natural, Sport Grey only (not dark colors)
- **C7 Torch Red:** White, Natural, Sport Grey only (not dark colors)
- **Variant B C5:** White, Natural, Sport Grey only (not Light Blue for new art)
- **Yellow C5:** Light Blue sale had no issues (mark)

---

## Hoodie playbook (2026-06-19) — Gildan 18500

Use this as the default setup for future Corvette hoodies unless data says otherwise.

### Design setup

- **Blank:** Unisex Heavy Blend Hooded Sweatshirt (`Gildan 18500`)
- **Decoration method:** **DTG** (do not use embroidery for distressed car art + fine details)
- **Scale rule:** if enlarging causes clipping, keep current full-visible size (no cropped edges)
- **Text rule:** remove micro paragraph text; use a short readable line/quote only
- **Quote style:** 1-2 lines max, strong enthusiast language, sans-serif, bold/regular (no script fonts)
- **Badge-safe:** no Chevrolet/Corvette logos or crossed-flags marks
- **Color rule:** lead with light colors for readability (White, Sand/Natural, Sport Grey, Light Blue if contrast holds)

### Mockup selection

- Primary image should be a clean front mockup where graphic is fully visible
- Include at least one flat front and one on-model front
- Avoid lifestyle-first hero images where print appears too small

### Pricing baseline (current test)

- S-XL: **$41.00**
- 2XL: **$44.00**
- 3XL: **$46.00**
- Profit snapshot at these prices: ~**$8.33-$8.74** per unit (about **19-20%** margin)
- Offsite ads toggle: **ON** at **12%** (do not raise to 15% unless conversion supports it)

### Shipping baseline (Printify/Etsy sync)

- Economy (US): **$7.39** — local delivery 4-8 business days
- Standard (worldwide): **$8.49** — local 2-5 business days, international 10-30 business days
- Keep default shipping-profile auto-assign unless a listing needs a custom profile

---

## Pipeline commands

**Collection design workflow (C5/C6/C7 color variants):**
1. Generate car art (no quote in AI prompt): `PYTHONPATH=. .venv/bin/python scripts/generate_*`
2. Overlay staggered quote (matches Laguna Blue layout): `.venv/bin/python scripts/overlay_collection_quote.py designs/<master>.png`
3. Printify export: `.venv/bin/python scripts/prepare_printify_exports.py designs/<master>.png --threshold 235`

Custom quote (4 lines): `--lines "Line1" "Line2" "Line3" "Line4"` or `--preset velocity-yellow`

```bash
# Tonight's priorities (reads this file + sales_log.csv — no Etsy API)
.venv/bin/python scripts/shop_daily_brief.py

# Regenerate Printify export (clean — no car surgery)
.venv/bin/python scripts/prepare_printify_exports.py designs/corvette/c6_variant_B_collection.png
.venv/bin/python scripts/prepare_printify_exports.py designs/corvette/c7_torch_red_collection.png --threshold 235

# Regenerate Torch Red C7 master
PYTHONPATH=. .venv/bin/python scripts/generate_c7_torch_red.py

.venv/bin/python scripts/prepare_printify_exports.py designs/corvette/c7_laguna_blue_collection.png --threshold 235

# Regenerate Laguna Blue C7 master
PYTHONPATH=. .venv/bin/python scripts/generate_c7_laguna_blue.py

# Atomic Orange C6 (generates + overlays quote automatically)
PYTHONPATH=. .venv/bin/python scripts/generate_c6_atomic_orange.py
.venv/bin/python scripts/prepare_printify_exports.py designs/corvette/c6_atomic_orange_collection.png --threshold 235

# Quote overlay only (after any collection master gen)
.venv/bin/python scripts/overlay_collection_quote.py designs/<master>.png
.venv/bin/python scripts/overlay_collection_quote.py designs/corvette/c7_velocity_yellow_collection.png --preset velocity-yellow

# Torch Red C5
PYTHONPATH=. .venv/bin/python scripts/generate_c5_torch_red.py
.venv/bin/python scripts/prepare_printify_exports.py designs/corvette/c5_torch_red_collection.png --threshold 235

# Black C5 (generates + overlays C5 quote automatically)
PYTHONPATH=. .venv/bin/python scripts/generate_c5_black.py
.venv/bin/python scripts/prepare_printify_exports.py designs/corvette/c5_black_collection.png --threshold 235

# Regenerate Etsy shop icon + banner
.venv/bin/python scripts/build_etsy_shop_assets.py
```

**Do not run:** `scripts/polish_c5_master.py` on masters without explicit request.

## Tycoon mission log

| When | Mission |
|------|------|
| 2026-07-16 11:08 | Write listing copy: C5 Variant B (~$21) → `c5_variant_B_blackwheels_plate_UPLOAD_TO_PRINTIFY.png` |
