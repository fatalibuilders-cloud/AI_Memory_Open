import { getDb } from "@/db";
import {
  DonationError,
  INTENT_LABELS,
  parseDonationInput,
  type DonationStatus,
  type Frequency,
  type Intent,
} from "./donation";
import { DEFAULT_CURRENCY, toCents } from "./money";
import { appUrl, getPaymentProvider } from "./payments";
import { newDonationReference } from "./reference";

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
}

export interface StartedDonation {
  reference: string;
  checkoutUrl: string;
  /** False when the built-in simulator handled the checkout — no money moved. */
  liveMode: boolean;
}

export async function createDonation(raw: unknown): Promise<StartedDonation> {
  const input = parseDonationInput(raw);
  const db = await getDb();

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

  const reference = newDonationReference();
  const provider = getPaymentProvider();

  await db.query(
    `INSERT INTO donations
       (reference, project_id, amount_cents, currency, frequency, intent,
        donor_name, donor_email, anonymous, dedication, message, status, provider)
     VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, 'pending', $12)`,
    [
      reference,
      projectId,
      input.amountCents,
      DEFAULT_CURRENCY,
      input.frequency,
      input.intent,
      input.donorName || null,
      input.donorEmail,
      input.anonymous,
      input.dedication || null,
      input.message || null,
      provider.name,
    ],
  );

  const base = appUrl();
  const session = await provider.createCheckout({
    reference,
    amountCents: input.amountCents,
    currency: DEFAULT_CURRENCY,
    frequency: input.frequency,
    description: describeDonation(projectName, input.intent),
    donorEmail: input.donorEmail,
    successUrl: `${base}/donate/thank-you?ref=${reference}`,
    cancelUrl: `${base}/donate?cancelled=${reference}`,
  });

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

/**
 * Settle a donation. Idempotent: a provider that retries its webhook, or
 * sends the same event twice, never double-counts a gift.
 */
export async function settleDonation(
  lookup: { reference?: string | null; providerRef?: string | null },
  status: "completed" | "failed",
): Promise<Donation | null> {
  const db = await getDb();
  const rows = await db.query<{ reference: string }>(
    `UPDATE donations
     SET status = $1,
         completed_at = CASE WHEN $1 = 'completed' THEN now() ELSE completed_at END
     WHERE status = 'pending'
       AND (($2::text IS NOT NULL AND reference = $2) OR ($3::text IS NOT NULL AND provider_ref = $3))
     RETURNING reference`,
    [status, lookup.reference ?? null, lookup.providerRef ?? null],
  );
  if (rows.length === 0) return null; // Unknown reference, or already settled.
  return getDonationByReference(rows[0].reference);
}

interface DonationRow {
  reference: string;
  project_id: string | null;
  project_name: string | null;
  project_slug: string | null;
  amount_cents: string | number;
  currency: string;
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
}

function toDonation(row: DonationRow): Donation {
  return {
    reference: row.reference,
    projectId: row.project_id,
    projectName: row.project_name,
    projectSlug: row.project_slug,
    amountCents: toCents(row.amount_cents),
    currency: row.currency,
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
  };
}
