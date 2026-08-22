# Professional approval marketplace, education & suppliers, daily log (2026-08-19)

Owner's request: onboard certified QS / architects / engineers to approve & stamp
architectural drawings, structural drawings and BOQ for a fee (app keeps 10%;
professionals hold a monthly platform "tier"); country-sync so each country's
professionals subscribe & earn; a tab where professionals earn; an education tab
for new clients; a suppliers tab for raw materials & finishes (app takes a
commission on purchases & referrals). Plus the earlier-approved daily progress
log. Built, tested (328 tests) & pushed — app @ main (commit cee367b).

## Built
1. **Professional approval marketplace** (the core)
   - Tables `professionals`, `approval_requests` (+ drizzle + BOOTSTRAP_SQL).
   - `lib/professionals.ts` — apply (self-declared registration, board resolved
     per country via REGULATORS: Kenya arch/QS→BORAQS, eng→EBK, +UG/TZ/NG/ZA),
     status pending→verified (admin only, never auto), monthly membership tier,
     `listAvailable(country, discipline)` = verified + paid-up match.
   - `lib/approvals.ts` — request → claim → approve/reject & **stamp** (records the
     professional's own `board + registrationNo`), fee split, earnings. Fee via
     `approvalFeeForCost` (arch/struct 0.5%, BOQ 0.4% of construction cost, KES
     floors); platform keeps `PLATFORM_APPROVAL_COMMISSION_PCT` (10%), pro gets 90%.
   - Routes: `/api/professionals` (apply), `/membership`, `/work` (claim|decide);
     `/api/projects/[id]/approvals` (GET/POST/DELETE); `/api/admin/professionals`.
   - Pages: `/professionals` (onboard + membership + earnings + open/assigned work),
     **Approval tab** on the project (client requests approval of the 3 docs;
     green-light banner when all approved), `/admin/professionals` verify queue.
   - Country-synced: a professional only ever sees work from their own country.
2. **Education tab** — `lib/education.ts` (18-term glossary + 4 how-to guides);
   public `/learn` page (also an acquisition surface).
3. **Supplier marketplace** — `suppliers` table + `lib/suppliers.ts` (apply →
   admin-activated; country/category listing); `/suppliers` directory + apply
   form; `SUPPLIER_COMMISSION_PCT` (5%); referral-attribution events
   (`supplier_referral`, `supplier_applied`, `approval_requested`).
4. **Daily programme log** — `DailyProgressLog` on the Progress tab: turns the
   labour schedule into a planned day-by-day timeline, shows where today falls
   against it, and logs each site day (reusing the build diary). Satisfies the
   earlier "daily logs to keep up with programme" request.
5. Nav: AccountMenu → Learn / Suppliers / Earn as a pro; admin → Professionals.

## Honesty line held
The app records **self-declared** registrations and facilitates the introduction
+ payment. It never certifies anyone and never stamps a document — "verified" is a
deliberate admin/board step, and every approval carries the *named professional's*
own stamp and registration. Supplier listings are admin-activated, not fabricated.

## Interpretation notes / owner to confirm
- "5% a month tier": modelled as a monthly professional **membership** (flat, env
  `PROFESSIONAL_MEMBERSHIP_KES`, default 1,500) alongside the precise 10% approval
  commission. `PROFESSIONAL_MEMBERSHIP_PCT`=0.05 kept as the headline service rate.
  Confirm whether the tier should be a flat fee or 5% of earnings.
- Approval fee %s and floors are indicative — a real board fee-scale or the
  professional's own quote should override; all env-configurable.
- Membership & approval payments run in **mock** mode until live keys are set
  (mock extends membership 30 days end-to-end). Payouts to professionals are
  settled off-platform per the professional agreement (no payout rail wired yet).

## Round 2 — open the marketplace to EVERY discipline (commit fdd7764, 330 tests)
Owner: "attract all kinds of professionals in construction industry."
- **Disciplines 3 → 16**: QS, architect, structural/civil/geotechnical/services
  (MEP)/electrical/mechanical engineers, land surveyor, construction manager,
  clerk of works, interior designer, landscape architect, physical planner, EIA
  expert, contractor — each with regulator per country (Kenya filled: EBK, BORAQS,
  LSB, NCA, IDAK, LAAK, PPB, NEMA).
- **Stampable documents 3 → 11**: + MEP, electrical, mechanical, civil,
  geotechnical, survey, physical-planning, environmental (each mapped to a
  discipline, own fee % + floor). Project Approval tab: statutory 3 + a "more
  approvals & consultant reports" toggle.
- **Professional directory** (`/directory`, `listVerifiedDirectory`): clients
  find/connect with ANY verified pro in their country, incl. non-stamping trades
  (PM, clerk of works, interior/landscape, contractor). Free listing = reward for
  verification; membership only gates paid approval jobs. Leads tracked
  (`professional_lead`) for routing. Nav: "Find a professional".
- **Supplier admin activation** (`/admin/suppliers` + `/api/admin/suppliers`):
  review & activate applications into the public marketplace. Admin nav link.
- Tier kept: flat monthly membership + 10% approval commission (predictable).

## Round 3 — close the money loop + notifications (commit 87838bc, 334 tests)
Owner: "both" (M-Pesa membership checkout + payouts, AND lead notifications).
- **Membership checkout**: new `professional_membership` product routed through the
  existing `createCheckout`/`completePurchase` machinery → works on mock + M-Pesa
  now, live gateway on callback later. On success `extendMembership` 30d + notify.
- **Approval-fee payment**: approval requests now start `pending_payment`; new
  `approval_fee` product priced from the request; on payment `markRequestPaid`
  publishes it to pros (`requested`) and alerts matching members. ApprovalsPanel
  redirects to checkout; "Pay fee" state. This is why requests are unpaid-first.
- **Payouts**: `owed` = approved-but-unpaid `payout_cents`; `/admin/payouts` +
  `/api/admin/payouts`; `settleProfessional` marks jobs `paid` (the ledger) and
  notifies the pro. Real disbursement = M-Pesa **B2C when wired** (env
  `MPESA_B2C_SHORTCODE`), else manual/owner-side.
- **Notifications** (email + SMS, mock-until-keys, best-effort): new approval job →
  matching members; directory lead → the pro (with client contact); approval
  decision → client; membership + payout → pro. Builders in notify.ts/sms.ts +
  `marketplace-notify.ts`; `professionalContact`/`availableContacts` lookups.
- Approval status set now: pending_payment → requested → assigned → approved →
  paid (payout settled); + rejected/cancelled.

## Round 4 — live M-Pesa Daraja STK + B2C (commit e3a0c76, 337 tests)
Owner pasted a Daraja consumer key + secret (advised to ROTATE — shared in chat;
never stored in repo, env only).
- **STK push (collection) is real now** (`mpesa.ts`): `getAccessToken` (cached
  OAuth), `stkPush` (Lipa na M-Pesa Online), `darajaBaseUrl` per env. The
  `/api/checkout/mpesa` route replaces the old 501 stub with a live push and
  stores the **CheckoutRequestID** on the pending purchase; the callback route now
  matches on CheckoutRequestID (how Daraja IDs the txn) and completes idempotently
  — so it grants ANY product: subscription, professional membership, paid approval
  request, verified build. Sandbox behaviour unchanged when keys absent.
- **B2C (payouts) implemented**: `b2cConfig`/`b2cConfigured`/`b2cPayment`. The
  `/admin/payouts` route disburses via B2C when configured + the pro has a Kenyan
  phone; else marks for manual send. Ledger settlement recorded regardless. Added
  `b2c-result` / `b2c-timeout` ack routes.
- Helpers: `getPurchaseForCharge`, `setPurchaseCheckoutRef`,
  `getPurchaseByCheckoutRef` on payments.ts.

## Still open
- Owner must add the remaining M-Pesa env (below) for STK to actually fire; STK
  also needs a real live-tested SHORTCODE + PASSKEY (consumer key/secret alone
  aren't enough). B2C needs the encrypted SECURITY_CREDENTIAL (Safaricom cert).
- **ROTATE the pasted Daraja key/secret** — they were shared in chat.
- Mock/M-Pesa success page returns to the generic success page (could deep-link
  back to the project/professional console).
- Seed real, vetted suppliers per country (deliberately not fabricated).
- Other countries' regulator maps cover only the core 4 disciplines.

## Round 5 — board auto-verify, expanded Learning, password recovery (commit f535226, 356 tests)
Owner: auto-update professionals by checking the board register (EBK) for a valid,
up-to-date membership; admit immediately if the registration matches the account
owner, but require an up-to-date board membership before earning; expand Learning
(materials, tests, who-does-what, QA, duties, formulas); add password recovery.
- **Board verification** (`lib/board-verify.ts`): pluggable — per-country/
  discipline/board endpoint via env (`BOARD_VERIFY_URL[_<...>]` + `_KEY`); no
  public EBK API exists, so when unset it returns null → professional stays
  PENDING (manual). Never fabricates "verified". Auto-admit on register-name match
  to the account owner (title/order-insensitive `namesMatch`). Records
  `board_verified` / `board_valid_until` / `board_checked_at` on professionals.
  `canTakeWork` now also requires `boardMembershipCurrent` (up-to-date licence).
  `/api/professionals/recheck` + console board panel + re-check button.
- **Learning** (`lib/education.ts` + `/learn`): MATERIALS, TESTS (with standards),
  ROLES (duties across 10 disciplines), QA_STAGES, and FORMULAS (quantities,
  concrete mixes, reinforcement incl. d²/162, loads & structure, survey, finishes,
  cost, conversions). Page has anchored sections + quick-nav.
- **Password recovery**: `password_resets` table; `createPasswordReset`/
  `resetPassword` in auth.ts (single-use, SHA-256-hashed, 1-hour tokens; drops all
  sessions on reset; no email enumeration). `/api/auth/forgot` + `/reset`;
  `/forgot` + `/reset/[token]` pages; login "Forgot password?" link; reset email.

## Board verification env (optional — enables auto-admit; else manual)
- `BOARD_VERIFY_URL_KENYA_STRUCTURAL_ENGINEER` (most specific) or
  `BOARD_VERIFY_URL_EBK` (per board) or `BOARD_VERIFY_URL` (global), plus a
  matching `BOARD_VERIFY_KEY*` bearer token. Endpoint receives
  `{country, discipline, board, registrationNo}` and returns JSON with any of
  `found/exists`, `name/registeredName`, `status`, `validUntil/expiry`,
  `upToDate/current/inGoodStanding`. No EBK public API today — connect a data
  source/agent when available; until then verification is manual via /admin.

## Env for go-live (owner) — set in Vercel, NOT the repo
- **STK (collection)**: `PAYMENTS_PROVIDER=mpesa`, `MPESA_CONSUMER_KEY`,
  `MPESA_CONSUMER_SECRET`, `MPESA_SHORTCODE` (Paybill/Till), `MPESA_PASSKEY`
  (Lipa na M-Pesa Online passkey), `MPESA_ENV=production` (or sandbox), `APP_URL`
  (for the callback). Optional `MPESA_TX_TYPE=till` for Buy Goods (default Paybill);
  `MPESA_CALLBACK_URL` to override. Callback: `/api/payments/mpesa/callback`.
- **B2C (payouts)**: `MPESA_B2C_SHORTCODE`, `MPESA_INITIATOR_NAME`,
  `MPESA_SECURITY_CREDENTIAL` (initiator password encrypted with Safaricom's prod
  cert). Result/timeout URLs default to `/api/payments/mpesa/b2c-result` &
  `/b2c-timeout` (override via `MPESA_B2C_RESULT_URL`/`MPESA_B2C_TIMEOUT_URL`).
- Fees/tiers (optional, sensible defaults): `PLATFORM_APPROVAL_COMMISSION_PCT`
  (0.10), `PROFESSIONAL_MEMBERSHIP_KES/USD`, `APPROVAL_FEE_PCT_*`/`_MIN_*`,
  `SUPPLIER_COMMISSION_PCT`.
- Notifications: `EMAIL_API_URL`/`EMAIL_API_KEY`/`EMAIL_FROM`; SMS provider keys.
- `ADMIN_EMAIL` gates the /admin/* verify/activate/payout screens.
