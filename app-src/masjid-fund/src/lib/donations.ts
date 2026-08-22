import { getDb } from "@/db";
import {
  DonationError,
  INTENT_LABELS,
  parseDonationInput,
  type DonationStatus,
  type Frequency,
  type Intent,
} from "./donation";
import { sendCancellation, sendReceipt } from "./email";
import { BASE_CURRENCY, DEFAULT_CURRENCY, fromBase, toCents, usdToKesRate } from "./money";
import { METHOD_CURRENCY, appUrl, getPaymentProvider, type PaymentMethod } from "./payments";
import { normalizeMsisdn } from "./payments/mpesa";
import { DONATION_LIMITS, countRecent, hashIp } from "./rate-limit";
import { newDonationReference, newManageToken } from "./reference";

/**
 * Donation lifecycle: record a pending gift, hand the donor to the payment
 * provider, then settle the row when the provider confirms. Nothing counts
 * towards a project total until it is settled.
 */

export interface Donation {
  reference: string;
  projectId: string | null;
  projectName: string | null;
  projectSlug: string | null;
  amountCents: number;
  currency: string;
  /** USD equivalent — what every published total is summed from. */
  baseAmountCents: number;
  fxRate: number;
  method: PaymentMethod;
  phone: string | null;
  /** The donor's receipt from the rail, e.g. an M-Pesa code. */
  externalRef: string | null;
  frequency: Frequency;
  intent: Intent;
  donorName: string | null;
  donorEmail: string;
  anonymous: boolean;
  dedication: string | null;
  message: string | null;
  status: DonationStatus;
  createdAt: string;
  completedAt: string | null;
  /** Secret in the donor's receipt that lets them manage a monthly gift. */
  manageToken: string | null;
  /** Provider's recurring-agreement id, once a monthly gift has started. */
  subscriptionRef: string | null;
  cancelledAt: string | null;
  receiptSentAt: string | null;
}

export interface StartedDonation {
  reference: string;
  checkoutUrl: string;
  /** False when the built-in simulator handled the checkout — no money moved. */
  liveMode: boolean;
}

export async function createDonation(
  raw: unknown,
  meta: { ip?: string | null } = {},
): Promise<StartedDonation> {
  const input = parseDonationInput(raw);
  const db = await getDb();

  const ipHash = meta.ip ? hashIp(meta.ip) : null;
  await assertWithinDonationLimits(input.donorEmail, ipHash);

  let projectId: string | null = null;
  let projectName: string | null = null;
  if (input.projectSlug) {
    const rows = await db.query<{ id: string; name: string; status: string }>(
      "SELECT id, name, status FROM projects WHERE slug = $1",
      [input.projectSlug],
    );
    if (rows.length === 0) {
      throw new DonationError("That project could not be found.", 404);
    }
    if (rows[0].status === "completed") {
      throw new DonationError(
        "This masjid is fully funded — please choose another project or give where it is needed most.",
        409,
      );
    }
    projectId = rows[0].id;
    projectName = rows[0].name;
  }

  // Zakat is never applied to construction. It is recorded without a project
  // so it stays in a separate pool for eligible recipients.
  if (input.intent === "zakat") {
    projectId = null;
    projectName = null;
  }

  // The donor names the gift in USD; the rail decides what they are charged.
  // Both figures are stored, along with the rate that linked them, so a receipt
  // and the ledger can never disagree later.
  const method = input.method;
  const currency = METHOD_CURRENCY[method];
  const chargedCents = fromBase(input.amountCents, currency);
  const fxRate = currency === BASE_CURRENCY ? 1 : usdToKesRate();

  let phone: string | null = null;
  if (method === "mpesa") {
    phone = normalizeMsisdn(input.phone ?? "");
    if (!phone) {
      throw new DonationError(
        "Enter the M-Pesa number to send the prompt to, for example 0722 000 000.",
        400,
      );
    }
  }

  const reference = newDonationReference();
  const provider = getPaymentProvider(method);
  // Monthly gifts carry a management secret from the start, so the receipt can
  // link straight to a cancel page without the donor needing an account.
  const manageToken = input.frequency === "monthly" ? newManageToken() : null;

  await db.query(
    `INSERT INTO donations
       (reference, project_id, amount_cents, currency, base_amount_cents, fx_rate, method, phone,
        frequency, intent, donor_name, donor_email, anonymous, dedication, message,
        status, provider, manage_token, ip_hash)
     VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,'pending',$16,$17,$18)`,
    [
      reference,
      projectId,
      chargedCents,
      currency,
      input.amountCents,
      fxRate,
      method,
      phone,
      input.frequency,
      input.intent,
      input.donorName || null,
      input.donorEmail,
      input.anonymous,
      input.dedication || null,
      input.message || null,
      provider.name,
      manageToken,
      ipHash,
    ],
  );

  const base = appUrl();
  let session;
  try {
    session = await provider.createCheckout({
      reference,
      amountCents: chargedCents,
      currency,
      frequency: input.frequency,
      description: describeDonation(projectName, input.intent),
      donorEmail: input.donorEmail,
      phone,
      successUrl: `${base}/donate/thank-you?ref=${reference}`,
      cancelUrl: `${base}/donate?cancelled=${reference}`,
    });
  } catch (err) {
    // The row exists but no payment was ever started — close it off rather than
    // leaving a pending donation that nothing will ever settle.
    await db.query("UPDATE donations SET status = 'failed' WHERE reference = $1", [reference]);
    throw err;
  }

  if (session.providerRef) {
    await db.query("UPDATE donations SET provider_ref = $1 WHERE reference = $2", [
      session.providerRef,
      reference,
    ]);
  }

  return {
    reference,
    checkoutUrl: session.checkoutUrl,
    liveMode: provider.liveMode,
  };
}

/**
 * Stolen cards are validated by firing many small donations at a form, so a
 * burst from one source is stopped before it reaches the payment provider —
 * where each attempt would cost a fee and count against the account's fraud
 * ratio. The wording stays neutral: a real donor who has hit the limit should
 * not be told they look like a criminal.
 */
async function assertWithinDonationLimits(email: string, ipHash: string | null): Promise<void> {
  const tooMany = new DonationError(
    "We have taken several donation attempts from here recently. Please wait a few minutes and try again, or email us and we will take it manually.",
    429,
  );

  const byEmail = await countRecent(
    "donations",
    "donor_email",
    email,
    DONATION_LIMITS.perEmail.minutes,
  );
  if (byEmail >= DONATION_LIMITS.perEmail.max) throw tooMany;

  if (!ipHash) return;
  const byIp = await countRecent("donations", "ip_hash", ipHash, DONATION_LIMITS.perIp.minutes);
  if (byIp >= DONATION_LIMITS.perIp.max) throw tooMany;
}

export function describeDonation(projectName: string | null, intent: Intent): string {
  const label = INTENT_LABELS[intent];
  return projectName ? `${projectName} — ${label}` : `Masjid Fund — ${label} (where most needed)`;
}

export async function getDonationByReference(reference: string): Promise<Donation | null> {
  const db = await getDb();
  const rows = await db.query<DonationRow>(
    `SELECT d.*, p.name AS project_name, p.slug AS project_slug
     FROM donations d LEFT JOIN projects p ON p.id = d.project_id
     WHERE d.reference = $1`,
    [reference],
  );
  return rows.length > 0 ? toDonation(rows[0]) : null;
}

export async function getDonationByManageToken(token: string): Promise<Donation | null> {
  const db = await getDb();
  const rows = await db.query<DonationRow>(
    `SELECT d.*, p.name AS project_name, p.slug AS project_slug
     FROM donations d LEFT JOIN projects p ON p.id = d.project_id
     WHERE d.manage_token = $1`,
    [token],
  );
  return rows.length > 0 ? toDonation(rows[0]) : null;
}

/**
 * Settle a donation. Idempotent: a provider that retries its webhook, or
 * sends the same event twice, never double-counts a gift.
 *
 * A completed gift triggers its receipt here — the one place every provider
 * path converges on.
 */
export async function settleDonation(
  lookup: {
    reference?: string | null;
    providerRef?: string | null;
    subscriptionRef?: string | null;
    externalRef?: string | null;
  },
  status: "completed" | "failed",
): Promise<Donation | null> {
  const db = await getDb();
  const rows = await db.query<{ reference: string }>(
    `UPDATE donations
     SET status = $1,
         completed_at = CASE WHEN $1 = 'completed' THEN now() ELSE completed_at END,
         subscription_ref = COALESCE($4, subscription_ref),
         external_ref = COALESCE($5, external_ref)
     WHERE status = 'pending'
       AND (($2::text IS NOT NULL AND reference = $2) OR ($3::text IS NOT NULL AND provider_ref = $3))
     RETURNING reference`,
    [
      status,
      lookup.reference ?? null,
      lookup.providerRef ?? null,
      lookup.subscriptionRef ?? null,
      lookup.externalRef ?? null,
    ],
  );
  if (rows.length === 0) return null; // Unknown reference, or already settled.

  const donation = await getDonationByReference(rows[0].reference);
  if (donation && status === "completed") await sendReceipt(donation);
  return donation;
}

/**
 * Cancel a monthly gift from the donor's own management link. Idempotent, and
 * tolerant of a provider that has already ended the agreement: the donor's
 * instruction is recorded either way.
 */
export async function cancelMonthlyGiving(token: string): Promise<Donation | null> {
  const donation = await getDonationByManageToken(token);
  if (!donation || donation.frequency !== "monthly") return null;
  if (donation.cancelledAt) return donation; // Already cancelled.

  if (donation.subscriptionRef) {
    try {
      await getPaymentProvider().cancelSubscription(donation.subscriptionRef);
    } catch (err) {
      // Record the instruction regardless — an agreement the provider has
      // already ended must not leave the donor stuck on this page.
      console.error(`cancelling ${donation.reference} at the provider failed:`, err);
    }
  }

  const db = await getDb();
  await db.query("UPDATE donations SET cancelled_at = now() WHERE reference = $1", [
    donation.reference,
  ]);

  const cancelled = await getDonationByReference(donation.reference);
  if (cancelled) await sendCancellation(cancelled);
  return cancelled;
}

/**
 * Record a gift that arrived outside the site — bank transfer, cash handed to
 * the committee, a cheque. Written as already completed, since the money is
 * in hand before anyone types it in.
 */
export async function recordOfflineDonation(input: {
  amountCents: number;
  projectSlug: string | null;
  donorName: string | null;
  donorEmail: string | null;
  intent: Intent;
  note: string | null;
  anonymous: boolean;
}): Promise<Donation> {
  const db = await getDb();

  let projectId: string | null = null;
  if (input.projectSlug) {
    const rows = await db.query<{ id: string }>("SELECT id FROM projects WHERE slug = $1", [
      input.projectSlug,
    ]);
    if (rows.length === 0) throw new DonationError("That project could not be found.", 404);
    projectId = rows[0].id;
  }

  const reference = newDonationReference();
  await db.query(
    `INSERT INTO donations
       (reference, project_id, amount_cents, currency, base_amount_cents, fx_rate, method,
        frequency, intent, donor_name, donor_email, anonymous, message, status, provider, completed_at)
     VALUES ($1, $2, $3, $4, $3, 1, 'offline', 'one_time', $5, $6, $7, $8, $9, 'completed', 'offline', now())`,
    [
      reference,
      projectId,
      input.amountCents,
      DEFAULT_CURRENCY,
      input.intent,
      input.donorName,
      input.donorEmail ?? "",
      input.anonymous,
      input.note,
    ],
  );

  const donation = await getDonationByReference(reference);
  if (donation && donation.donorEmail) await sendReceipt(donation);
  return donation!;
}

interface DonationRow {
  reference: string;
  project_id: string | null;
  project_name: string | null;
  project_slug: string | null;
  amount_cents: string | number;
  currency: string;
  base_amount_cents: string | number | null;
  fx_rate: string | number | null;
  method: string | null;
  phone: string | null;
  external_ref: string | null;
  frequency: string;
  intent: string;
  donor_name: string | null;
  donor_email: string;
  anonymous: boolean;
  dedication: string | null;
  message: string | null;
  status: string;
  created_at: string | Date;
  completed_at: string | Date | null;
  manage_token: string | null;
  subscription_ref: string | null;
  cancelled_at: string | Date | null;
  receipt_sent_at: string | Date | null;
}

function toDonation(row: DonationRow): Donation {
  return {
    reference: row.reference,
    projectId: row.project_id,
    projectName: row.project_name,
    projectSlug: row.project_slug,
    amountCents: toCents(row.amount_cents),
    currency: row.currency,
    baseAmountCents: toCents(row.base_amount_cents ?? row.amount_cents),
    fxRate: Number(row.fx_rate ?? 1),
    method: (row.method ?? "card") as PaymentMethod,
    phone: row.phone,
    externalRef: row.external_ref,
    frequency: row.frequency as Frequency,
    intent: row.intent as Intent,
    donorName: row.donor_name,
    donorEmail: row.donor_email,
    anonymous: row.anonymous,
    dedication: row.dedication,
    message: row.message,
    status: row.status as DonationStatus,
    createdAt: new Date(row.created_at).toISOString(),
    completedAt: row.completed_at ? new Date(row.completed_at).toISOString() : null,
    manageToken: row.manage_token,
    subscriptionRef: row.subscription_ref,
    cancelledAt: row.cancelled_at ? new Date(row.cancelled_at).toISOString() : null,
    receiptSentAt: row.receipt_sent_at ? new Date(row.receipt_sent_at).toISOString() : null,
  };
}
