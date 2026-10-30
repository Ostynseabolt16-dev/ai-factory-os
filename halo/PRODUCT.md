# Halo — salon booking for one chair

Competitor wedge vs [GlossGenius](https://glossgenius.com/pricing) (Standard ≈ **$24–28/mo** annual/monthly; Gold **$48–56**; Platinum **$148–168** + **2.6%** payments).

## Verdict

Yes — compete on a **narrow wedge**, not feature parity.

GlossGenius is a full beauty OS (booking site, POS, inventory, marketing texts, payroll, AI, medspa EMR) with **100k+** businesses. Matching that stack means payments (PCI/Stripe Connect), SMS deliverability, chargebacks, and years of salon edge cases.

**Halo** targets the person who made you ask: a solo stylist / booth renter who mostly needs clients to book, pay a deposit, and show up.

## Wedge

| | GlossGenius Standard | Halo (target) |
|---|---|---|
| Who | Solo → multi-location beauty OS | One pro, one chair |
| Price | ~$25–28/mo + 2.6% | **$0–12/mo** + Stripe rate, or free + slightly higher take |
| Surface | App + template site + POS | Beautiful public booking link + phone-first day view |
| Complexity | 100+ features | Book · deposit · remind · rebook |

## MVP scope (this prototype)

1. Marketing landing (why switch / why not need the full OS)
2. Client booking page (services → day → time → confirm)
3. Stylist “today” board (local demo data)

Not in v1: real payments, SMS, inventory, multi-staff, payroll, AI receptionist.

## Go-to-market test

1. Offer your stylist a free branded booking page for 30 days.
2. If she uses it and clients book without texting her, the product is real.
3. Only then wire Stripe deposits + reminder texts.

## Run locally

```bash
cd halo
npm install
npm run dev
```

Routes: `/` marketing · `/book/mara` client book · `/app` stylist day view
