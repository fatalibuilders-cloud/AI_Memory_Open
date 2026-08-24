import { NextRequest, NextResponse } from "next/server";
import { settleDonation } from "@/lib/donations";
import { getPaymentProvider } from "@/lib/payments";

/**
 * Where PayPal sends the donor after they approve. Approval is not money, so
 * this is where we capture it — then hand them to their receipt.
 *
 * A failure here is not the end of the gift: the PAYMENT.CAPTURE.COMPLETED
 * webhook still settles it, so the donor is sent to the receipt page either
 * way and sees "awaiting confirmation" for the moment it takes.
 */
export async function GET(req: NextRequest) {
  const orderId = req.nextUrl.searchParams.get("token"); // PayPal's name for it
  const reference = req.nextUrl.searchParams.get("ref");

  if (orderId) {
    try {
      const provider = getPaymentProvider("paypal");
      const event = await provider.capture?.(orderId);
      if (event) {
        await settleDonation(
          {
            reference: event.reference,
            providerRef: event.providerRef ?? orderId,
            externalRef: event.externalRef,
          },
          event.status,
        );
      }
    } catch (err) {
      console.error(`paypal capture for order ${orderId} failed:`, err);
    }
  }

  const destination = reference
    ? `/donate/thank-you?ref=${encodeURIComponent(reference)}`
    : "/donate";
  return NextResponse.redirect(new URL(destination, req.url), 303);
}
