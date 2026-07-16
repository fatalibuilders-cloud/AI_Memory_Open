# Oware Legends — Monetization Model

**Principle:** monetize *generosity and identity*, never *frustration*. Games that respect African players' data budgets and wallets earn the retention that makes any monetization work. Everything below is optional for the player; the game is 100% playable free, forever.

---

## 1. Market reality (design constraints, not afterthoughts)

| Constraint | Consequence for us |
|---|---|
| Card penetration is low; **mobile money is dominant** (M-Pesa, MTN MoMo, Airtel Money, Orange Money) | IAP must work via mobile-money aggregators (Flutterwave, Paystack, DPO), not only Play Billing |
| Data is expensive per MB in many markets | Game is <40 KB, offline-first; ads must be **opt-in rewarded only** (player chooses to spend data) |
| Low-end Android dominates (1–2 GB RAM) | No heavy engine; plain WebView/HTML5 wrapped in a tiny APK/TWA |
| ARPU is lower, but scale is enormous and growing | Volume + ad-fill strategy first, IAP whales second |
| Airtime is a de-facto currency | Airtime billing (carrier billing) is a first-class checkout option via aggregators |

## 2. Revenue streams (in priority order)

### 2.1 Rewarded video ads (primary, ~60–70% of revenue)
- **Where:** "Double your coins" after a match; "+1 streak shield" once/day; bonus theme discount.
- **Never:** forced interstitials, banners during play, ads for children-flagged accounts beyond policy limits.
- **Networks:** AdMob primary; AppLovin/Unity mediation for fill in markets where AdMob fill is weak.
- The hook is already in code: `Monetization.showRewardedAd(cb)` in `index.html`.

### 2.2 Cosmetic IAP (secondary, ~20–30%)
- Board themes (Savanna/Coast/Sahara/Midnight shipped; roadmap: national-pride themes for Nigeria, Ghana, Kenya, Senegal, Côte d'Ivoire, Ethiopia, South Africa launched around AFCON/national days).
- Seed skins (cowrie shells, gemstones, bronze weights).
- Coin packs ($0.49 / $0.99 / $2.99 tiers — priced in local currency equivalents).
- Hook in code: `Monetization.purchase(productId, cb)`.

### 2.3 Tournament passes (growth phase)
- Weekly city/country leaderboard tournaments; small entry via coins (earnable free) with cosmetic + coin prizes.
- Sponsored tournaments (telcos, banks, beverage brands love pan-African cultural moments) — clean brand placement on the tournament screen only.

### 2.4 "Support the game" patron tier
- One-time or monthly small contribution ("Buy the makers a meal"), gives a patron badge next to the player name. Surprisingly effective with culturally proud titles.

## 3. What we will NOT do
- No pay-to-win (AI difficulty, matchmaking, and rules are never purchasable).
- No loot boxes / gacha / gambling mechanics — also a legal risk in several African jurisdictions.
- No energy systems that lock people out of playing.
- No dark-pattern "limited time!" pressure on children.

## 4. Unit economics sketch (validate in soft launch)

Assumptions for a Kenya/Nigeria/Ghana soft launch (verify with live data — see Risk-Registry):
- Rewarded eCPM: $1.5–4.0 blended; 1.2 rewarded views/DAU opt-in
- IAP conversion: 0.5–1.5% of MAU, ARPPU ~$1.2
- Target: **$8–20 revenue per 1,000 DAU/day** blended at soft launch; break-even vs. server costs is trivial because the core game is serverless/offline.

## 5. Payments integration order
1. Google Play Billing (required for Play Store distribution).
2. Flutterwave or Paystack checkout (web build) → unlocks M-Pesa, MoMo, Airtel Money, cards, airtime.
3. Direct Daraja (M-Pesa) integration only if aggregator fees justify it at scale.

## 6. Compliance notes
- Families Policy / age screens for ad networks (many players will be minors).
- Local advertising-standard rules (e.g., no gambling-adjacent creatives in NG/KE).
- Data protection: NDPR (Nigeria), POPIA (South Africa), Kenya DPA — trivial today (no accounts, local storage only); revisit when leaderboards land.
