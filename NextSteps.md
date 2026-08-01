# Next Steps — AI Memory System (Root Level)

> **SCOPE:** This file tracks pending work on the **AI Memory system itself** — its structure, standards, policies, shared resources, and cross-project infrastructure. This is NOT a project-level file. Project-specific next steps live in each project's own `NextSteps.md`.

**Last Updated:** 2026-08-01

---

## Priority Queue

### High Priority

1. **Create a Deriv API token and verify the setup** *(owner action — [Human])*. Run `./setup.sh` in `app-src/deriv-crypto-bot/` (creates the environment and a `.env`). Then in your Deriv account: **Settings → API token**, scopes **Read + Trade only** (not Payments, not Admin), created while on your **virtual/demo** account. Put it in `.env` — that file is git-ignored, never commit it. Then run `python -m deriv_bot.check`, which verifies everything and **places no trades**. It also prints the real payout ratio to use in step 2.
2. **Backtest against real Deriv history** *(owner action — [Human], needs the token from step 1)*. `python -m deriv_bot.backtest --symbol cryBTCUSD --days 30 --save-candles btc.json`. Run it across several months and several coins. Compare **win rate against breakeven win rate** — with the default 0.85 payout you must beat 54.1% just to break even. On synthetic random-walk data the strategy correctly shows a loss, so assume no edge until real data says otherwise.
3. **Run the bot in dry-run, then demo, before considering real money** *(owner action — [Human])*. `DERIV_DRY_RUN=true python -m deriv_bot` shows what it would trade without trading. Observe both winning and losing days first.
4. **Begin FatalibuildersConstructionApp Release 1.0 development** — Project initialized (2026-07-16). Next session: use the project's own `agents/open.md`, start CORE-1.0 (scaffold the `fatalibuilders-app` repository, pure [AI]). *(Project-level work — root NextSteps tracks only that the project is active.)*
5. ~~Owner sign-off / staging~~ **DONE (2026-07-16):** owner approved; PROJECT_MEMORY_INIT executed; staging archived.
6. ~~Tool inventory~~ *Mostly done: Excel-only accounting; WhatsApp + calls.* Photo storage/scheduling questions now only matter if Epic 5 (management features) stays.

### Medium Priority

1. **Continue FatalibuildersConstructionApp staging Documents 1 & 2** — After owner review: fill goals, success metrics, constraints; decide mobile-first vs. web-first and offline support. *(Project-level work — use the staging project's own agents/open.md.)*
2. **Register API keys** — **No longer urgent: release 1 needs NO keys** (Excel and wa.me WhatsApp links are key-free). Guide at `API-Keys-Guide.md`; first real key will be the hosting account at launch.
3. **Confirm enterprise OS** — Remaining deferred setup field; Zoho One has a pre-built MCP connector if chosen.
4. ~~Add backtesting to `deriv-crypto-bot`~~ **DONE (2026-08-01):** `deriv_bot/backtest.py` replays history through the same strategy and risk code. See the follow-up in High Priority — the tool exists, but no real Deriv history has been run through it yet.
5. **Decide whether `deriv-crypto-bot` becomes a formal project** — Currently standalone source under `app-src/`. If it grows beyond a personal tool, stage it via `staging.md` and promote it with `PROJECT_MEMORY_INIT.md`.

### Low Priority

1. **Standards customization** — CC/DE v2.0 and ACS v1.0 adopted as-is; customize reporting cadence, financial thresholds, or communication preferences in a future session if desired.

---

## Recently Completed

| Item | Date | Notes |
|------|------|-------|
| Stage FatalibuildersConstructionApp project | 2026-07-16 | Full staging structure created per staging.md; 36 agent files distributed to 9 departments; drafts flagged for owner review |
| Run `setup-AI-Memory.md` (one-time system setup) | 2026-07-16 | Owner, fork URL, and model preferences configured; API keys, enterprise OS, and standards customization deferred to owner |
| Record app integration directive | 2026-07-16 | Owner: integrate with all kinds of tools → integration-first architecture; Document 2 now In Progress |
| Owner full name confirmed; contact profile created | 2026-07-16 | Eng Ali Ahmed — owner fields updated system-wide; preliminary profile at `contacts/Eng-Ali-Ahmed.md` |
| Build `deriv-crypto-bot` | 2026-08-01 | Crypto-only, 24/7 trading bot for the Deriv WebSocket API at `app-src/deriv-crypto-bot/`. Demo-account default, daily loss limit, kill switch. Awaits owner API token |
| Add backtesting to `deriv-crypto-bot` | 2026-08-01 | `deriv_bot/backtest.py` replays history through the same strategy and risk code; reports win rate against the breakeven implied by payout. On synthetic random-walk data the defaults correctly show a loss — no edge demonstrated yet on real data |
| Onboarding, CI, and a reconnection fix | 2026-08-01 | `deriv_bot/check.py` preflight (never trades; prints the measured payout ratio), `setup.sh`, and CI on Python 3.10/3.11/3.12. Running the check exposed a real bug: socket-open failures escaped the trader's reconnect loop, so a rejecting proxy would have crashed the bot rather than retrying. Fixed and covered. 221 tests passing |

---

*This is a root-level system file. It tracks work on the AI Memory system, NOT individual projects.*
