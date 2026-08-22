import { NextRequest, NextResponse } from "next/server";
import { settleDonation } from "@/lib/donations";
import { getPaymentProvider } from "@/lib/payments";

/**
 * Daraja posts the result of an STK push here.
 *
 * Unlike Stripe, this callback carries no signature, so it is treated as an
 * untrusted hint rather than an instruction: the only thing acted on is the
 * CheckoutRequestID, and it settles a donation only if we are already waiting
 * on that exact id. A callback for an unknown id changes nothing.
 *
 * Restrict this path to Safaricom's published IP ranges at the edge as well —
 * the application cannot verify the caller on its own.
 *
 * Safaricom retries until it gets a 200, so we acknowledge everything we can
 * parse and record what mattered.
 */
export async function POST(req: NextRequest) {
  const rawBody = await req.text();

  try {
    const event = await getPaymentProvider("mpesa").parseWebhook(rawBody, req.headers);
    if (!event) {
      return NextResponse.json({ ResultCode: 0, ResultDesc: "Ignored" });
    }

    const donation = await settleDonation(
      {
        reference: event.reference,
        providerRef: event.providerRef,
        externalRef: event.externalRef,
      },
      event.status,
    );

    if (!donation) {
      // Unknown, or already settled — either way there is nothing to do, and
      // Safaricom must still be told to stop retrying.
      console.warn(`mpesa callback for unmatched request ${event.providerRef}`);
    }
    return NextResponse.json({ ResultCode: 0, ResultDesc: "Accepted" });
  } catch (err) {
    console.error("mpesa callback failed:", err);
    // A non-zero result asks Safaricom to retry, which is what we want when the
    // failure was ours (a database blip) rather than the payload's.
    return NextResponse.json({ ResultCode: 1, ResultDesc: "Retry" }, { status: 500 });
  }
}
