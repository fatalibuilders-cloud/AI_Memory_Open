import { NextResponse } from "next/server";
import { getDonationByReference } from "@/lib/donations";

/**
 * Receipt lookup by reference. Deliberately narrow: the donor's email and
 * message are never returned, so a guessed reference reveals nothing personal.
 */
export async function GET(
  _req: Request,
  { params }: { params: Promise<{ reference: string }> },
) {
  const { reference } = await params;
  const donation = await getDonationByReference(reference);
  if (!donation) {
    return NextResponse.json({ error: "No donation found with that reference." }, { status: 404 });
  }
  return NextResponse.json({
    reference: donation.reference,
    status: donation.status,
    amountCents: donation.amountCents,
    currency: donation.currency,
    frequency: donation.frequency,
    intent: donation.intent,
    projectName: donation.projectName,
    projectSlug: donation.projectSlug,
    createdAt: donation.createdAt,
    completedAt: donation.completedAt,
  });
}
