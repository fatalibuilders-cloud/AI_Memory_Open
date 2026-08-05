# Launch Readiness Synthesis — Fatalibuilders / "Msingi"

**For:** Eng Ali Ahmed · **Date:** 2026-08-02
**Sources combined:** (1) Msingi Global Success Roadmap · (2) Msingi Global Execution Blueprint · (3) Provecta Group — Market Gap & Readiness Review (13-gap analysis)

> Note on naming: the reports call the product **"Msingi"** (a Provecta Group framing). It is the same product as the Fatalibuilders Construction App. **Open question for the owner:** is the app being (re)branded "Msingi", or does Fatalibuilders remain the name? This only affects logo/copy, not the build.

---

## 1. What the three reports agree on

- **The market position is real and unoccupied:** "type your dimensions once on your phone → engineering-grade quantities + a costed local-currency BOQ + a labour plan, on a chosen design code, for a one-time fee." Enterprise QS suites are desktop/expensive; Western SME tools are subscriptions; the two African apps miss the core. The unserved buyer is the **self-builder** (~4 in 5 Kenyan homes are self-built; only 776 registered QSs).
- **The wedge is COMPLETENESS, not "a better calculator":** a quick per-m² quote silently omits **29–98%** of true cost (finishes, fittings, services). Showing that gap is "the sharpest reason a self-builder pays."
- **Two moats are hard to copy and already built:** the dimensions-in → BOQ engine, and the design-code (Eurocode + national annex) profiles.
- **Launch path (Success Roadmap / Blueprint Phase 1):** finish payments, accounts, exports, testing, analytics, and the free teaser → then Kenya launch via partnerships → East Africa → Africa → global. KPIs: 100k users year 1, >40% MAU, <5 min estimate, >95% satisfaction.

---

## 2. Honest reconciliation — reports vs. ACTUAL build (2026-08-02)

The reviews were dated ~1 Aug and marked several items as "still to build." Since then we've closed most. Reconciled status:

| # | Market need (review) | Review status | **Actual build now** |
|---|---|---|---|
| 1 | Dimensions → itemised BOQ | ✅ built | ✅ built, 95 tests |
| 2 | Mobile-first (phone) | ✅ | ✅ PWA + wizard |
| 3 | Design-code intelligence | ✅ | ✅ Eurocode/BS/KEBS profiles, stamped |
| 4 | Completeness / anti-under-quote | ✅ "fires live" | ✅ **NOW REAL** — services+fittings added; shell-vs-hidden % reveal shipped |
| 5 | Current local rate data | ◑ | ✅ Fatali 2026 rate card (multi-region later) |
| 6 | Affordable one-time pricing | ◑ designed | ✅ $30 + working checkout |
| 7 | Free teaser (trust before pay) | ⬜ | ✅ materials + completeness free; BOQ/exports paid |
| 8 | Mobile-money (M-Pesa) | ⬜ launch-critical | ✅ **NOW BUILT** — Daraja STK provider (mock-until-keys) |
| 9 | Accounts + entitlement | ⬜ | ✅ built |
| 10 | Branded exports + disclaimer | ⬜ | ✅ Excel + PDF, per-page disclaimer |
| 11 | Diaspora "Verified Build" tier | ⬜ post-MVP | Planned (R2+) |
| 12 | Lender-ready BOQ + QS sign-off | ⬜ post-MVP | Planned (R2+) |
| 13 | Materials-marketplace handoff | ⬜ post-MVP | Planned (R2+) |

**Headline:** every launch-critical gap the review named (#4, #7, #8, #10) is now built. The MVP is functionally complete in sandbox.

**Roadmap Phase-1 checklist (both the Execution Blueprint and Success Roadmap):** payments ✅, accounts ✅, PDF/Excel exports ✅, free teaser ✅, testing ✅, **analytics ✅**. Beyond Phase-1, several roadmap items are now also built:
- **Multiple currencies (Phase 3/8):** KES locally + USD internationally.
- **Multi-language (East Africa → global phase):** now **five languages — English, Kiswahili, Français, Español, العربية (Arabic, RTL)**. Dependency-free i18n (`src/i18n/`): a locale registry (endonym + text direction) + typed dictionaries; `<html dir>` follows the locale so Arabic renders right-to-left; a header dropdown switches language. **Adding another language = one registry entry + one dictionary** (the `Dictionary` type makes the compiler reject an incomplete translation; a parity test double-checks every locale). **Full app coverage:** header, footer, homepage, pricing, paywall, account, login/signup, offline page, the project wizard (all steps, field labels, select options, review, buttons) and the legal pages (terms/privacy/refund, with a governing-language "English prevails" note). *(Only the cost-engine BOQ line-item labels and export files remain English — a small future batch.)*
- **Offline capability (competitive advantage):** PWA service worker + offline fallback (`public/sw.js`, `public/offline.html`, `OfflineReady`) **and** true **offline project editing** — IndexedDB drafts + a sync outbox (`offline-store.ts`, `offline-sync.ts`) wired into the wizard: edits persist and queue with no signal, then flush automatically on reconnect.

Phase-1 is complete in code; what remains is owner-gated (keys, hosting, email, legal) or later-phase (partnerships, AI, marketplace).

> **Offline scope (be honest):** app-shell offline + offline data editing now both work — the wizard keeps working offline and syncs on reconnect (a previously-visited edit page is served from SW cache so it reopens offline; `/api` always stays live when online). Not covered: opening a *brand-new* project while fully offline from a cold start, and multi-device conflict resolution (latest-write-wins per project) — later refinements, not blockers.

---

## 3. Problems resolved this session (the reason for this doc)

1. **Completeness wedge made real (#4).** The BOQ previously stopped at finishes. It now includes **Electrical** and **Plumbing & fittings** line items (from your 2026 rate card), and the product shows a **"a quick quote would hide ~X% of your true cost"** panel — shell cost vs hidden (finishes+services+fittings) vs true all-in. This is shown to **free users and on the public /demo** as the conversion hook; the itemised BOQ stays behind the $30. This directly implements the reviews' single most-important strategic point.
2. **M-Pesa built (#8) — the launch-critical Kenyan payment.** The reviews are blunt: "M-Pesa is universal; card-only fails." We now have a Daraja STK-push provider behind the same payment abstraction as Paddle — a phone-number checkout page, initiate route, and callback handler — working in sandbox now, activating with your Daraja keys. **Card (Paddle) is the secondary rail; M-Pesa is primary for Kenya.**

---

## 4. What still stands between us and a live launch (all owner-gated)

Ordered by the reviews' Phase-1 priority:

1. **Kenyan payment keys** (primary) — **recommended: Pesapal** (aggregator, M-Pesa + cards, settles to KCB, live in days). Integration is **built + tested**; just add keys per `Pesapal-Activation-Guide.md`. Lower-fee alternative: your own Daraja shortcode per `Mpesa-Activation-Guide.md` (`MPESA_*` + `PAYMENTS_PROVIDER=mpesa`).
2. **Paddle keys** (secondary, worldwide cards) — already pre-built; see `Paddle-Activation-Guide.md`.
3. **Hosting + Postgres** (Vercel + Neon) — gives the public URL; see `TESTING-GUIDE.md`.
4. **Email provider** (Resend) — verification + receipts.
5. **Owner legal review** — Terms/Privacy/Refund drafts.
6. ~~**Analytics** (Blueprint Phase 1) — signup→estimate→purchase funnel.~~ ✅ **BUILT** — first-party funnel + owner-only `/admin` dashboard (set `ADMIN_EMAIL`). No third-party trackers.
7. **Owner-engineer validation** of the new **services/fittings assumptions** (counts per m²) — like the earlier materials sign-off.

Once M-Pesa keys + hosting exist, the app is sellable in Kenya.

---

## 5. Post-MVP moats (sequenced, per the reports)

- **Diaspora "Verified Build" tier ($50–150)** — highest willingness-to-pay, sharpest pain (fraud). Biggest single revenue lever.
- **Lender-ready BOQ + registered-QS sign-off** — turns the construction-loan gate into a distribution channel.
- **Materials-marketplace handoff** — BOQ → priced cart with a supplier partner, on revenue share.
- **Daily-use hooks** (Blueprint Phase 4): daily material prices, labour rates, weather, project diary, reminders — to drive the >40% MAU KPI.
- **AI assistant** (Phase 3): drawing OCR/analysis, BOQ automation, cost optimisation.

These map to Releases 2–4 already in the plan.

---

## 6. Recommended immediate sequence

1. Owner: **Daraja (M-Pesa) sandbox signup** + **Vercel/Neon** — the two things that unblock a live Kenyan test.
2. AI (ready now): wire real M-Pesa STK once keys land; add analytics; write the M-Pesa activation guide; confirm services/fittings assumptions with the owner.
3. Soft launch in Kenya to a small group (the reviews' Phase 2: hardware stores, QS/engineers, universities) → weekly feedback.

*Build state: app repo `fatalibuilders-cloud/fatalibuilders-app` @ main, 95 tests. Memory: this file + `Master-AI-Context.md` + release plan.*
