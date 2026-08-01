import { NextRequest, NextResponse } from "next/server";
import { settleDonation } from "@/lib/donations";
import { getPaymentProvider } from "@/lib/payments";

/**
 * Simulated settlement for the built-in test provider — the button on the
 * fake checkout page posts here. Refuses to run whenever a real provider is
 * configured, so it can never settle a live donation.
 */
export async function POST(req: NextRequest) {
  const provider = getPaymentProvider();
  if (provider.liveMode) {
    return NextResponse.json({ error: "Not available." }, { status: 404 });
  }

  const form = await req.formData();
  const reference = String(form.get("reference") ?? "");
  const outcome = form.get("outcome") === "failed" ? "failed" : "completed";
  if (!reference) {
    return NextResponse.json({ error: "Missing reference." }, { status: 400 });
  }

  await settleDonation({ reference }, outcome);

  const redirectTo =
    outcome === "completed"
      ? `/donate/thank-you?ref=${encodeURIComponent(reference)}`
      : `/checkout/${encodeURIComponent(reference)}?failed=1`;
  return NextResponse.redirect(new URL(redirectTo, req.url), 303);
}
