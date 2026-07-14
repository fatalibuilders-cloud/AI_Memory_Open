# Decision: Added Entry-Condition Filters Inspired by Reference EA, Researched Independently

**Date:** 2026-07-14
**Owner:** Founder (fatalibuilders@gmail.com)

---

## What Happened

Founder shared a screenshot of a third-party commercial EA's ("ForexEA v2.2") MT4 settings panel and asked to research the settings on the web and add equivalent elements to AITrader's signal logic. **Only the input panel was visible in the screenshot — not that product's source code or real underlying logic**, so nothing here reproduces that product; it's independently-researched implementations of well-known retail-EA filter concepts, inspired by the parameter *names* shown.

## Research Findings

- **Volume/Volatility/Range filters** are standard, well-documented retail-EA risk/selectivity tools: volume filters avoid illiquid periods, volatility filters avoid both dead markets and abnormal spikes, range filters help EAs be selective about trending vs. choppy conditions (sources in the web search — see chat for links).
- **"Weekend Protection" / Friday-close / Monday-start** patterns are standard in prop-firm-oriented EAs, protecting against weekend gap risk (positions held over a market close can open at a very different price Monday).
- **"AI Filter"** in commercial retail EAs is frequently marketing branding for a rule-based or simplistic weighted-heuristic filter, not necessarily real machine learning — confirmed by research into similar products (e.g., an EA using Bill Williams' Accelerator/Decelerator oscillators, weighted, branded "Artificial Intelligence"). Found no evidence "AI Filter" implies genuine trained ML in general industry practice.
- **"Deposit Acceleration"** is not a standard/documented term — appears specific to this product's marketing, likely referring to increasing position size as the account grows (functionally similar to "Auto Lot Sizing," already a separate toggle in the reference panel).

## What Was Added to `Product_Development/MQL5_EA/AITrader.mq5` (v0.20)

- `PassesVolumeFilter()` — current bar volume vs. recent average
- `PassesVolatilityFilter()` — ATR ratio band (rejects dead + spike conditions)
- `PassesRangeFilter()` — ADX trend-strength gate (paired to suit our trend-following placeholder signal, not a range-scalping strategy)
- `PassesDataFeedSanityCheck()` — spread/stale-quote sanity check
- `IsWeekendEntryBlocked()` / `ApplyWeekendCloseAll()` — weekend gap-risk protection (genuinely new capability, not present in prior drafts)

All are toggleable inputs, matching the reference panel's true/false style, and all fail open (don't block trading) on data-lookup errors to avoid silently freezing the EA.

## What Was Deliberately NOT Added

1. **"AI Filter" branding.** `GetSignalConfidence()` remains an explicit stub — renaming it "AI" without a real trained model would repeat the same unsubstantiated-claim risk already flagged in the Legal & Marketing epic (2026-07-14j). If real ML-based signal scoring is wanted, that's a separate, substantial model-training project, not a rebrand.
2. **The reference EA's 3.1 fixed lot size / "Deposit Acceleration" concept.** Contradicts AITrader's carefully-decided dynamic risk-based lot sizing (starting at 0.01, derived from stop-loss tier and stop distance) — not adopted.
3. **The reference account's performance as a benchmark.** The screenshot showed roughly $5,000 → $31,600 in about 2 days (+533%). This is the same order of magnitude as the "$50→$1,000/day" framing already ruled out earlier in this project as unrealistic and a red flag for marketing/regulatory purposes (2026-07-14j). It most plausibly reflects the oversized fixed lot size (3.1 lots on a $5,000 account) catching a favorable short run, not a repeatable, safe edge. Flagged explicitly so it isn't mistaken for validation of anything.

## Open Items / Follow-ups

- All new filters are still paired with the placeholder EMA/RSI signal — they improve entry *selectivity*, not the fundamental lack of a real signal-generation strategy (still the top open item, per 2026-07-14n).
- Filter thresholds (volume average period, volatility ratio bounds, ADX threshold, spread/staleness limits, weekend hours) are reasonable defaults, not backtested or tuned — need validation once real backtesting is possible.
- Not compiled or backtested, same caveat as 2026-07-14n.
