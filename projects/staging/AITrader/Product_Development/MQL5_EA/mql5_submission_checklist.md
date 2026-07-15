# MQL5 Market Submission Checklist — FatalibuildersTrader Super Scalpers

**Purpose:** Everything MQL5 Market requires for submission, what's done, what's missing, and what I can vs. can't produce in this environment.

---

## Blocking — must happen before submission is even worth attempting

| Item | Status | Who does it |
|---|---|---|
| EA compiles cleanly in MetaEditor | ❌ Not done | You / a developer with MT5 installed |
| Real backtest via MT5 Strategy Tester | ❌ Not done | You / a developer |
| Real entry-signal logic (replaces placeholder) | ❌ Not done | Dedicated design work — the single biggest gap |
| Safe Mode confidence model (replaces stub) | ❌ Not done | Depends on real signal logic existing first |

MQL5's own review runs an automated Strategy Tester pass and a manual check for programming errors — a placeholder-signal, uncompiled EA will not pass this, or will pass and mislead buyers, which is worse.

## Seller account

| Item | Status | Who does it |
|---|---|---|
| MQL5 Seller registration | ❌ Not started | You — requires identity verification, ~10 business days review |

## Listing assets

| Item | Status | Who does it |
|---|---|---|
| Product description text | ✅ Draft written — `mql5_listing_description.md` | Done, needs final numbers once backtested |
| Logo image, 200×200 | ❌ Not producible here | I have no image-generation tool in this environment — see spec below |
| Logo image, 140×140 | ❌ Not producible here | Same |
| Logo image, 60×60 | ❌ Not producible here | Same |
| Product "Type" field selection | ⏳ Decision, not a file | You — pick the correct EA category on the MQL5 form |
| Verified backtest/performance data to attach | ❌ Not producible here | Only exists once real backtesting happens |

### Logo spec (hand this to a designer, or use Canva/similar yourself)

- Three PNG files at exactly 200×200, 140×140, and 60×60 pixels
- Should read clearly at the smallest size (60×60) — avoid fine detail or small text
- No claims or numbers baked into the image (avoid anything that could later conflict with the no-guarantee marketing rule)
- Suggested concept: a simple mark representing the product name/initials, not literal chart/candlestick clip art (overused in this category, doesn't differentiate)

## Legal/compliance (from earlier sessions, still applies)

| Item | Status |
|---|---|
| No multiplier/guarantee claims anywhere in listing | ✅ Draft description follows this |
| Risk disclosure included | ✅ In draft description |
| IP/commercial counsel review of ToS/licensing language | ❌ Not done — still recommended (2026-07-14j) |
| Confirm no CTA/investment-adviser registration trigger | ❌ Not done |

---

## What I explicitly cannot do, and why

- **Cannot compile or backtest** — MetaEditor and MT5's Strategy Tester are Windows desktop applications; I run in a sandboxed cloud environment with no GUI access to them.
- **Cannot generate the logo images** — no image-generation tool is available to me here (checked before writing this).
- **Cannot log into MetaTrader 5 or MQL5.com and complete the upload as "the developer,"** even if given credentials — I have no browser/remote-desktop connection to those systems, and separately, I wouldn't recommend sharing live MT5 account or MQL5 seller credentials with an AI agent in a chat session. That's a real account with real money/identity behind it; credential hygiene matters regardless of who's asking. If you want hands-on help with the actual upload, that's a job for you directly, or a developer/freelancer you vet and grant scoped access to (e.g., a temporary MQL5 collaborator role, if that exists on their platform) — not something to hand over via chat.

## What I can still help with from here

- Refining the description text once real backtest numbers exist
- Drafting the ToS/licensing language for counsel to review
- Continuing to build out the EA's remaining logic (signal design, confidence model, adaptive parameters) so there's something real to compile and test
- Reviewing compile errors or Strategy Tester output if you paste them back to me
