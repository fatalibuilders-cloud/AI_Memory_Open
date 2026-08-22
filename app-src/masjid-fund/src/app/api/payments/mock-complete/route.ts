import { NextRequest, NextResponse } from "next/server";
import { getDonationByReference, settleDonation } from "@/lib/donations";
import { getPaymentProvider } from "@/lib/payments";

/**
 * Simulated settlement for the built-in test provider — the button on the fake
 * checkout, and on the M-Pesa rehearsal page, posts here. It refuses to run
 * whenever the rail that took this donation is a real one, so it can never
 * settle a live payment.
 */
export async function POST(req: NextRequest) {
  const form = await req.formData();
  const reference = String(form.get("reference") ?? "");
  const outcome = form.get("outcome") === "failed" ? "failed" : "completed";
  if (!reference) {
    return NextResponse.json({ error: "Missing reference." }, { status: 400 });
  }

  const donation = await getDonationByReference(reference);
  if (!donation || getPaymentProvider(donation.method).liveMode) {
    return NextResponse.json({ error: "Not available." }, { status: 404 });
  }

  await settleDonation({ reference }, outcome);

  const failedPath =
    donation.method === "mpesa"
      ? `/donate/mpesa/${encodeURIComponent(reference)}`
      : `/checkout/${encodeURIComponent(reference)}?failed=1`;
  const redirectTo =
    outcome === "completed"
      ? `/donate/thank-you?ref=${encodeURIComponent(reference)}`
      : failedPath;
  return NextResponse.redirect(new URL(redirectTo, req.url), 303);
}
