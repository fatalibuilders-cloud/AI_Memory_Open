# Fatalibuilders AI MVP: chat, calculators, investment analyser, account roles (2026-08-31)

Owner pasted the **FATALIBUILDERS AI — MVP v1.0** product spec (AI chat as the
heart of the app; standalone calculators; cost estimator; investment analyser;
account types at signup; site reports; AI inspection; document generator; DB
schema; a strong honesty-first system prompt; tool-call architecture; usage
control + subscription tiers; admin dashboard; security rules) with the
instruction **"absorb and implement what we don't have already"**.

Approach: surveyed the existing code first (BOQ/cost/structural engines, PDFs,
subscriptions, admin, `ai_usage` tiers all already existed) and built ONLY the
genuine gaps that form the deterministic, honesty-first backbone + the AI that
orchestrates it. Built, tested (**821 tests green**), tsc + lint clean,
production build OK, pushed — app repo branch
`claude/fatalibuilders-ai-mvp-round6` (commit a692c10).

## Built
1. **Deterministic calculators** (`src/lib/calculators.ts`) — concrete, masonry,
   plaster, flooring, roofing, painting, excavation quantity take-offs.
   - Constants `BAG_VOLUME_M3=0.0347`, `DRY_FACTOR=1.54`; `parseMixRatio`.
   - Each returns `CalcResult` = `{inputs, outputs, assumptions[], note}` with a
     PRELIMINARY note. `runCalculator(kind, input)` dispatcher coerces string
     inputs (so the API/AI can pass raw JSON). `CALCULATORS` map + `isCalculator`.
   - API `POST /api/calculators/[kind]` (session-gated); UI `/calculators`
     (`CalculatorsView`, per-kind field map, renders outputs + assumptions).
2. **Investment analyser** (`src/lib/investment.ts`) — `analyseInvestment`:
   total investment, gross/effective income, opex, **NOI**, cash flow after debt,
   gross/net yields, **payback years** (null if NOI≤0), **break-even occupancy**,
   and an occupancy **sensitivity** table [70/80/90/100%].
   - API `POST /api/invest`; UI `/invest` (`InvestmentView`).
3. **Account roles at signup** — `ACCOUNT_ROLES` = homeowner, contractor,
   engineer, quantity_surveyor, architect, developer, investor, supplier.
   `signup()` now takes + stores `role` on `users.role`; `SafeUser.role`;
   `AuthForm` shows a role `<select>` in signup mode; `/api/auth/signup` passes it.
4. **Fatalibuilders AI** (`src/lib/ai/*`) — the assistant at the heart.
   - `system-prompt.ts` — `FATALIBUILDERS_SYSTEM_PROMPT`: 10 honesty rules (never
     fabricate figures/standards; distinguish verified/user/calculated/assumption/
     preliminary; never represent output as an approved/sealed design; identify
     the standard used; use the project's country/region; **do all arithmetic via
     tools**; be concise; safety questions → physical inspection by a licensed pro).
   - `tools.ts` — `AI_TOOLS` (run_calculator, estimate_construction_cost,
     material_price_benchmark, analyse_investment) + `runTool()` dispatcher wired to
     `runCalculator`, `analyseInvestment`, and market benchmarks. Returns JSON.
   - `client.ts` — `@anthropic-ai/sdk` **manual tool-calling loop** (max 6 iters);
     model `CLAUDE_MODEL` env default `claude-opus-5`; `aiConfigured()` checks
     `ANTHROPIC_API_KEY`. `mockChat()` offline fallback detects concrete/paint/
     tile/cost intents by regex and runs the matching tool — so the assistant is
     **demoable and testable with no key**. Returns
     `{reply, inputTokens, outputTokens, toolCalls, model, mock}`.
   - `conversation.ts` — persistence + metering + cap. `monthlyLimit(paid)`
     (free = env `AI_MONTHLY_FREE` || 20; paid = env `AI_MONTHLY_LIMIT` || 0=∞),
     `monthlyUsage`, `listMessages` (owner-scoped), `sendMessage()` enforces the
     cap (429), loads history, calls `chat`, persists user+assistant `ai_messages`,
     writes a `usage_records` row with an estimated cost (`PRICING` $/1M map).
   - API `POST /api/ai/chat`; UI `/ai` (`AiChat` — suggestions, offline amber
     banner when `!aiConfigured()`). Nav: AccountMenu → Ask Fatalibuilders AI /
     Calculators / Investment analyser.
5. **DB** (`schema.ts`): new `ai_conversations`, `ai_messages` (+ `tool_calls`
   jsonb), `usage_records` (tokens + estimated_cost) with indexes; `users.role`
   column. All via `IF NOT EXISTS` in BOOTSTRAP_SQL + drizzle.

## Honesty line held (the core of the spec)
**Formulas live in code, not the prompt.** The model only orchestrates: it must
call `run_calculator` / `analyse_investment` for any number, so figures are
deterministic and reproducible, never hallucinated. The system prompt forbids
fabricating figures/standards and forbids representing output as an approved or
sealed design — every result is labelled PRELIMINARY and defers the real,
sealed work to a licensed professional (consistent with the approval marketplace).

## Tests
- `calculators.test.ts` (8): exact take-off assertions (concrete 10×0.3×0.2 →
  0.6 m³; excavation → 30/37.5; painting 10×3 → 30 m²/6 L; flooring 5×4 →
  20/22/62 tiles; masonry openings deduction; string coercion).
- `investment.test.ts` (3): worked example land 8M/con 25M/other 3M/rent 280k/
  occ 90/opex 25 → total 36M, NOI 2.268M, gross 9.33%, net 6.3%, payback 15.9;
  break-even 50% at debt 900k.
- `ai/ai.test.ts` (6): runTool concrete/cost-range/NOI; offline conversation
  persists the exchange + meters usage (mock=true, monthlyUsage=1, 2 messages);
  monthly free cap (AI_MONTHLY_FREE=1 → 2nd send 429); cross-user isolation.

## Staged / NOT yet built from the spec (candidates for follow-up)
The owner said "implement what we don't have already" — I built the deterministic
backbone + AI chat. Remaining spec items, deliberately deferred:
- AI **site report** generator; AI **site inspection** (photo/vision analysis).
- **Document generator** (quotation, tender, invoice, payment certificate,
  variation order, meeting minutes, method statement, risk assessment, handover).
- **Business** subscription tier (KSh 7,500) — Free/Pro already exist.
- Project **dashboard tool grid** and the "wow moment" project-creation flow.

## Owner to set for go-live (Vercel env, NOT the repo)
- `ANTHROPIC_API_KEY` (turns the AI from offline/mock → live conversational).
- `CLAUDE_MODEL` (default `claude-opus-5`), `AI_MONTHLY_FREE` (20),
  `AI_MONTHLY_LIMIT` (paid; 0 = unlimited).
- Everything else (calculators, investment, roles) works with no config.
