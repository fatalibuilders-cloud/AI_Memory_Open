import { NextRequest, NextResponse } from "next/server";
import { settleDonation } from "@/lib/donations";
import { PaymentError, getPaymentProvider } from "@/lib/payments";

/**
 * PayPal settlement callback. Verification is an API call back to PayPal —
 * the signature is a certificate chain, not an HMAC — so an unverifiable
 * payload is refused rather than trusted.
 */
export async function POST(req: NextRequest) {
  const rawBody = await req.text();

  try {
    const event = await getPaymentProvider("paypal").parseWebhook(rawBody, req.headers);
    if (!event) return NextResponse.json({ received: true, handled: false });

    const donation = await settleDonation(
      {
        reference: event.reference,
        providerRef: event.providerRef,
        externalRef: event.externalRef,
      },
      event.status,
    );
    // A null result means unknown or already settled — both fine to ack, or
    // PayPal retries an event we have already applied.
    return NextResponse.json({ received: true, handled: donation !== null });
  } catch (err) {
    if (err instanceof PaymentError) {
      return NextResponse.json({ error: err.message }, { status: err.status });
    }
    console.error("paypal webhook handling failed:", err);
    return NextResponse.json({ error: "Webhook could not be processed." }, { status: 400 });
  }
}
