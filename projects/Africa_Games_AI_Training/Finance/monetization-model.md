# Africa Games — Monetization Model

**Applies to:** **Market Day** (match-3 flagship) and **Oware Legends** (strategy). Where they differ, Market Day's model is called out — a match-3 monetizes very differently from a board game.

**Principle:** monetize *generosity, impatience and identity* — never *frustration*. Games that respect African players' data budgets and wallets earn the retention that makes any monetization work. Everything below is optional; both games are fully playable free, forever, and Market Day's Relax Mode is unlimited and never gated.

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
Rewarded video carries the model in low-ARPU markets: the player spends attention instead of money, and chooses to.

**Market Day placements (all opt-in, all live in code):**
| Placement | Reward | Why it converts |
|---|---|---|
| Level failed, one move short | **+5 moves**, continue the level | The highest-intent moment in the entire genre |
| Level complete | **Double the coins** | Feels like a gift, not a toll |
| Out of lives | **Refill all 5 hearts** | The alternative to waiting or paying |
| Shop, any time | **+50 coins** | Gives non-payers a path to every booster |

**Oware Legends:** "double your coins" after a match; daily streak bonus.

- **Never:** forced interstitials, banners during play, or ads beyond policy limits on children-flagged accounts.
- **Networks:** AdMob primary; AppLovin/Unity mediation where AdMob fill is weak.
- Hook in code: `Monetization.showRewardedAd(cb)`.

### 2.2 IAP (secondary, ~25–35% — higher for Market Day than Oware)
Match-3 sells *convenience and impatience*; a board game can only sell identity. Market Day therefore carries the heavier IAP mix.

**Market Day (shipped in the prototype shop):**
- Coin packs — $0.99 (500), $2.49 (1,500 + 5 hammers), $5.99 (4,000 + 15 boosters).
- Life refills (100 coins) — also earnable free via ad.
- Boosters: hammer (50 coins), shuffle (30 coins), +5 moves.
- Roadmap: pre-level booster loadouts, national-pride board cloths around AFCON/national days.

**Oware Legends:** cosmetic board themes and seed skins only — no gameplay advantage is ever sold.

- Hook in code: `Monetization.purchase(productId, cb)`.

### 2.2b The lives economy (Market Day only)
5 hearts, one spent per campaign attempt, **refunded on a win**, one regenerating per 10 minutes on a wall-clock timer. This is the genre's standard session-pacing and monetization engine, and refusing it would gut the business model (decision #11).

It is kept non-exploitative by three rules, all shipped:
1. **Relax Mode is unlimited and life-free** — nobody is ever locked out of playing.
2. A refill is always available for **free** via a rewarded ad, not only for money.
3. Winners keep their heart, so skilled play is never taxed.

### 2.3 Tournament passes (growth phase)
- Weekly city/country leaderboard tournaments; small entry via coins (earnable free) with cosmetic + coin prizes.
- Sponsored tournaments (telcos, banks, beverage brands love pan-African cultural moments) — clean brand placement on the tournament screen only.

### 2.4 "Support the game" patron tier
- One-time or monthly small contribution ("Buy the makers a meal"), gives a patron badge next to the player name. Surprisingly effective with culturally proud titles.

## 3. What we will NOT do
- No pay-to-win — skill, difficulty and rules are never purchasable. Boosters are conveniences that are all earnable free.
- No loot boxes / gacha / gambling mechanics — also a legal risk in several African jurisdictions.
- **No lockout without a free way out.** *(Revised 2026-08-30, decision #11: the original stance was "no energy systems at all". Market Day's campaign does use lives, because the genre's pacing and economics depend on them. The commitment is now narrower and specific: every gate has a free path — a rewarded ad, or the wait — and **Relax Mode is always unlimited and life-free**, so no player is ever locked out of playing the game.)*
- No dark-pattern "limited time!" pressure on children.
- No selling a way past a level the player has not earned (no "skip level" product).

## 4. Unit economics sketch (validate in soft launch)

Assumptions for a Kenya/Nigeria/Ghana soft launch (verify with live data — see Risk-Registry):

| Metric | Market Day (match-3) | Oware Legends |
|---|---|---|
| Rewarded eCPM (blended) | $1.5–4.0 | $1.5–4.0 |
| Rewarded views / DAU | **2.5–4.0** (four placements, high-intent "+5 moves" moment) | 1.0–1.5 |
| IAP conversion (of MAU) | 1.0–2.0% | 0.5–1.5% |
| ARPPU | ~$2.0 | ~$1.2 |
| **Revenue / 1,000 DAU / day** | **$20–45** | $8–20 |

Market Day carries roughly 2–3× the monetization of the board game on the same audience — which is exactly why it is the flagship. Break-even against infrastructure is trivial for both: the games are serverless and offline, so the only real costs are UA and development.

**The number that decides the business:** cost per install against 30-day revenue per install. Nothing else should be scaled until per-level fail rates and D7 retention are instrumented (see NextSteps #8).

## 5. Payments integration order
1. Google Play Billing (required for Play Store distribution).
2. Flutterwave or Paystack checkout (web build) → unlocks M-Pesa, MoMo, Airtel Money, cards, airtime.
3. Direct Daraja (M-Pesa) integration only if aggregator fees justify it at scale.

## 6. Compliance notes
- Families Policy / age screens for ad networks (many players will be minors).
- Local advertising-standard rules (e.g., no gambling-adjacent creatives in NG/KE).
- Data protection: NDPR (Nigeria), POPIA (South Africa), Kenya DPA — trivial today (no accounts, local storage only); revisit when leaderboards land.
