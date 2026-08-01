import { NextRequest, NextResponse } from "next/server";
import { settleDonation } from "@/lib/donations";
import { PaymentError, getPaymentProvider } from "@/lib/payments";

/**
 * Settlement endpoint for the configured payment provider. The raw body is
 * read as text because signature verification is computed over the exact
 * bytes the provider signed.
 */
export async function POST(req: NextRequest) {
  const rawBody = await req.text();
  try {
    const event = await getPaymentProvider().parseWebhook(rawBody, req.headers);
    if (!event) return NextResponse.json({ received: true, handled: false });

    const donation = await settleDonation(
      { reference: event.reference, providerRef: event.providerRef },
      event.status,
    );
    // A null result means unknown or already settled — both are fine to ack,
    // otherwise the provider retries an event we have already applied.
    return NextResponse.json({ received: true, handled: donation !== null });
  } catch (err) {
    if (err instanceof PaymentError) {
      return NextResponse.json({ error: err.message }, { status: err.status });
    }
    console.error("webhook handling failed:", err);
    return NextResponse.json({ error: "Webhook could not be processed." }, { status: 400 });
  }
}
