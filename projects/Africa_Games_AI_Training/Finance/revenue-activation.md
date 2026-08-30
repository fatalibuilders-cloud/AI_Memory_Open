# Revenue Activation — how Nairobi Wild actually starts paying

**Status: the code is finished. The accounts are not.**

Every earning path in the game is built, tested and wired. Nothing charges anyone yet because `monetization.js` ships with empty IDs and `testMode: true` — deliberately, so play-testing never risks a real charge or an invalid-traffic ban. This document is the checklist that turns it on.

**The honest summary:** a website cannot take money by itself. Revenue needs *your* accounts — you own the identity, the bank details and the tax status, and no one else can create them for you. Below is exactly what to open, in what order, what each one pays, and where the money lands.

---

## The five revenue streams, and what each needs

| # | Stream | Built? | Still needs | Realistic share |
|---|---|---|---|---|
| 1 | Rewarded video ads | ✅ 4 placements live | AdMob account + ad unit ID | **60–70%** |
| 2 | Coin & booster IAP | ✅ catalogue + checkout | Play Console **or** Flutterwave key | 20–30% |
| 3 | Mobile money (M-PESA) | ✅ checkout coded | Flutterwave/Paystack account | included above |
| 4 | Tip jar ("Support the makers") | ✅ in the shop | same as #2 | 3–8% |
| 5 | Sponsored / brand stages | ⬜ future | an audience first | later |

---

## Step 1 — AdMob (do this first; it earns without a store listing)

Ads are the engine in low-ARPU markets: the player spends attention, not money, and chooses to.

1. Create a Google AdMob account at `admob.google.com` (needs a Google account and a payment profile with your bank details).
2. Add the app, then create **one Rewarded ad unit**. Copy the App ID and the Rewarded unit ID.
3. Paste both into `monetization.js` → `CONFIG.admob`.
4. **Leave `testMode: true` until the app is actually published.** Clicking your own live ads is the fastest way to get an AdMob account banned permanently.
5. Turn `testMode: false` at launch.

**Payment threshold:** AdMob pays out once you pass **$100**, by bank transfer, roughly 21 days after month end. Below $100 it rolls over.

**The four placements already in the game** (each reports its name to the analytics hook, so you will know which one earns):

| Placement | Where | Why it converts |
|---|---|---|
| `continue` | Out of moves, one short | The highest-intent moment in the genre |
| `double` | Stage complete | Feels like a gift, not a toll |
| `lives` | Out of hearts | The free alternative to waiting or paying |
| `shop` | Any time, +50 coins | Gives non-payers a route to every booster |

---

## Step 2 — Taking payments

Two routes. **Do both eventually; start with whichever you can open faster.**

### Route A — Google Play Billing (needed for the Play Store)
1. Google Play Console developer account — **one-off $25**.
2. Create in-app products with IDs matching the catalogue **exactly**: `coins_500`, `coins_1500`, `bundle_big5`, `lives_refill`, `support_small`, `support_big`.
3. Set `CONFIG.play.enabled = true`.
4. Ship as a Trusted Web Activity — the code already uses the **Digital Goods API**, which is how a TWA reaches Play Billing.

**Google's cut:** 15% on the first $1M/year, 30% above. Payouts monthly to your bank.

### Route B — Flutterwave or Paystack (M-PESA, the web build)
This matters more than Route A in Kenya. Most players do not have a card; they have M-PESA.

1. Open a Flutterwave or Paystack merchant account (needs ID and a Kenyan bank account or M-PESA till).
2. Copy the **public** key into `CONFIG.web.publicKey` and set `CONFIG.web.provider`.
3. Add the checkout script to the page (`checkout.flutterwave.com/v3.js` or `js.paystack.co/v1/inline.js`) — the code loads it only when someone actually buys, so non-payers never download it.
4. Set `CONFIG.web.usdToLocal` to your real rate. Prices already display in KES.

**Fees:** roughly **1.4–3.8%** per transaction, settled to your bank or M-PESA, typically T+1 to T+3.

> **Never commit a secret key.** Only the *public* key belongs in this file. Secret keys live on a server, and this game has no server — which is also why there is no server-side receipt verification yet (see Risks).

---

## Step 3 — Ship it, because none of this pays while the game is unlisted

The single largest blocker to revenue is not code, it is distribution:

1. **Play Store listing** — $25, a privacy policy URL, a content rating, and store art.
2. **A privacy policy is mandatory** once ads are in. AdMob collects an advertising ID. The game itself stores nothing on a server, which makes the policy short and honest.
3. **Families Policy** — expect a large number of minor players. Configure ad content ratings accordingly, or the listing gets pulled.

---

## What the money might actually look like

Modelled per **1,000 daily players**, blended, at soft-launch quality. These are planning figures to be replaced with live data, not promises.

| Line | Assumption | Per 1,000 DAU/day |
|---|---|---|
| Rewarded ads | 2.5–4.0 views/DAU at $1.5–4.0 eCPM | **$8–24** |
| IAP + tips | 1–2% of players, ~$2 ARPPU | **$12–20** |
| **Total** | | **$20–45/day** |

At 10,000 daily players that is roughly **$200–450 a day** gross, before Google's cut and processor fees.

**The number that decides everything** is not revenue per player, it is **cost per install against 30-day revenue per install**. Do not spend a shilling on user acquisition until per-stage fail rates and D7 retention are instrumented — the difficulty curve is still hand-set and unvalidated (`Risk-Registry.md` #10).

**Infrastructure cost is ~zero.** The game is serverless and offline; there is nothing to pay for but development and marketing.

---

## Order of operations

1. **AdMob account** → paste IDs → the biggest stream is armed.
2. **Play Console $25** → create the six products → wrap as a TWA.
3. **Flutterwave/Paystack** → public key → M-PESA works for the web build.
4. **Publish**, with a privacy policy and a families-appropriate ad config.
5. **Instrument** fail rates and retention. Only then consider paid acquisition.

## What is deliberately not sold
No skipping stages, no buying difficulty, no loot boxes, no gambling mechanics, and no gate without a free path (an ad or a wait). Relax Mode is unlimited and free forever. This is a commercial decision as much as an ethical one: those mechanics attract regulatory attention in several African markets and burn the trust that retention depends on.
