import { getDb } from "@/db";
import type { Donation } from "@/lib/donations";
import { getOrg } from "@/lib/org";
import { appUrl } from "@/lib/payments";
import { ConsoleProvider } from "./console";
import { ResendProvider } from "./resend";
import type { EmailMessage, EmailProvider } from "./provider";
import { cancellationEmail, receiptEmail } from "./templates";

export * from "./provider";

let provider: EmailProvider | null = null;

/** Resend when RESEND_API_KEY is present, otherwise log-only. */
export function getEmailProvider(): EmailProvider {
  if (!provider) {
    const key = process.env.RESEND_API_KEY;
    provider = key
      ? new ResendProvider(
          key,
          process.env.EMAIL_FROM ?? "Masjid Fund <receipts@masjidfund.example>",
          process.env.EMAIL_REPLY_TO,
        )
      : new ConsoleProvider();
  }
  return provider;
}

/** Test-only: forget the resolved provider so env changes take effect. */
export function resetEmailProviderForTests(): void {
  provider = null;
}

/**
 * Send and record the outcome. Delivery failures are logged, never thrown:
 * a donation that has been paid must not be rolled back because a mail
 * service was briefly unavailable.
 */
async function deliver(
  message: EmailMessage,
  kind: string,
  reference: string | null,
): Promise<boolean> {
  const mailer = getEmailProvider();
  let status = "sent";
  let error: string | null = null;

  try {
    await mailer.send(message);
    if (!mailer.live) status = "logged";
  } catch (err) {
    status = "failed";
    error = err instanceof Error ? err.message : String(err);
    console.error(`email ${kind} to ${message.to} failed:`, err);
  }

  try {
    const db = await getDb();
    await db.query(
      `INSERT INTO email_log (recipient, subject, kind, donation_reference, status, error, provider)
       VALUES ($1, $2, $3, $4, $5, $6, $7)`,
      [message.to, message.subject, kind, reference, status, error, mailer.name],
    );
  } catch (err) {
    console.error("could not write email_log:", err);
  }

  return status !== "failed";
}

export async function sendReceipt(donation: Donation): Promise<boolean> {
  const base = appUrl();
  const sent = await deliver(
    receiptEmail(donation, getOrg(), {
      manageUrl:
        donation.frequency === "monthly" && donation.manageToken
          ? `${base}/giving/${donation.manageToken}`
          : null,
      projectUrl: donation.projectSlug ? `${base}/projects/${donation.projectSlug}` : null,
    }),
    "receipt",
    donation.reference,
  );

  if (sent) {
    const db = await getDb();
    await db.query("UPDATE donations SET receipt_sent_at = now() WHERE reference = $1", [
      donation.reference,
    ]);
  }
  return sent;
}

export async function sendCancellation(donation: Donation): Promise<boolean> {
  return deliver(cancellationEmail(donation, getOrg()), "cancellation", donation.reference);
}
