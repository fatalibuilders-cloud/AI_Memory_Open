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

## Still open
- Live Daraja **STK push** for the approval-fee/membership charge is still the
  intentional 501 stub in `/api/checkout/mpesa` (sandbox completes instantly);
  wire the real STK HTTP when Daraja keys are set.
- **M-Pesa B2C** disbursement not implemented — settle marks paid + notifies;
  owner sends the money until B2C creds wired.
- Where the mock/M-Pesa success page returns to after membership/approval_fee is
  the generic success page (fine for MVP; could deep-link back to the project).
- Seed real, vetted suppliers per country (deliberately not fabricated).
- Other countries' regulator maps cover only the core 4 disciplines.

## Env for go-live (owner)
- Payments: `PAYMENTS_PROVIDER=mpesa`, Daraja `MPESA_CONSUMER_KEY/SECRET/
  SHORTCODE/PASSKEY/ENV`, `APP_URL`; B2C: `MPESA_B2C_SHORTCODE` (+ B2C creds).
- Fees/tiers (all optional, sensible defaults): `PLATFORM_APPROVAL_COMMISSION_PCT`
  (0.10), `PROFESSIONAL_MEMBERSHIP_KES/USD`, `APPROVAL_FEE_PCT_*`/`_MIN_*`,
  `SUPPLIER_COMMISSION_PCT`.
- Notifications: `EMAIL_API_URL`/`EMAIL_API_KEY`/`EMAIL_FROM`; SMS provider keys.
- `ADMIN_EMAIL` gates the /admin/* verify/activate/payout screens.
