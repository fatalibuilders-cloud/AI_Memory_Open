import { createHmac, timingSafeEqual } from "crypto";
import {
  PaymentError,
  type CheckoutRequest,
  type CheckoutSession,
  type PaymentProvider,
  type SettlementEvent,
} from "./provider";

/**
 * Stripe Checkout over the REST API — no SDK dependency, so the deployment
 * stays small and the request shape is visible in one place. Active only when
 * STRIPE_SECRET_KEY is set; otherwise the app falls back to the simulator.
 *
 * One-time gifts use mode=payment; monthly gifts use mode=subscription with an
 * inline monthly price.
 */
export class StripeProvider implements PaymentProvider {
  readonly name = "stripe";
  readonly liveMode = true;

  constructor(
    private readonly secretKey: string,
    private readonly webhookSecret: string | undefined,
    private readonly apiBase = "https://api.stripe.com",
  ) {}

  async createCheckout(request: CheckoutRequest): Promise<CheckoutSession> {
    const subscription = request.frequency === "monthly";
    const params: Record<string, string> = {
      mode: subscription ? "subscription" : "payment",
      success_url: request.successUrl,
      cancel_url: request.cancelUrl,
      client_reference_id: request.reference,
      customer_email: request.donorEmail,
      "metadata[reference]": request.reference,
      "line_items[0][quantity]": "1",
      "line_items[0][price_data][currency]": request.currency.toLowerCase(),
      "line_items[0][price_data][unit_amount]": String(request.amountCents),
      "line_items[0][price_data][product_data][name]": request.description,
    };
    if (subscription) {
      params["line_items[0][price_data][recurring][interval]"] = "month";
      params["subscription_data[metadata][reference]"] = request.reference;
    } else {
      params["payment_intent_data[metadata][reference]"] = request.reference;
    }

    const res = await fetch(`${this.apiBase}/v1/checkout/sessions`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${this.secretKey}`,
        "Content-Type": "application/x-www-form-urlencoded",
        "Idempotency-Key": request.reference,
      },
      body: new URLSearchParams(params).toString(),
    });

    const body = (await res.json().catch(() => ({}))) as {
      id?: string;
      url?: string;
      error?: { message?: string };
    };
    if (!res.ok || !body.url) {
      throw new PaymentError(
        body.error?.message ?? "The payment provider could not start this donation.",
        502,
      );
    }
    return { checkoutUrl: body.url, providerRef: body.id ?? null };
  }

  async parseWebhook(rawBody: string, headers: Headers): Promise<SettlementEvent | null> {
    if (!this.webhookSecret) {
      throw new PaymentError("Webhook secret is not configured", 500);
    }
    const signature = headers.get("stripe-signature");
    if (!verifyStripeSignature(rawBody, signature, this.webhookSecret)) {
      throw new PaymentError("Signature verification failed", 400);
    }

    const event = JSON.parse(rawBody) as {
      type?: string;
      data?: { object?: { id?: string; client_reference_id?: string; metadata?: Record<string, string> } };
    };
    const object = event.data?.object ?? {};
    const reference = object.client_reference_id ?? object.metadata?.reference ?? null;
    const providerRef = object.id ?? null;

    switch (event.type) {
      case "checkout.session.completed":
      case "checkout.session.async_payment_succeeded":
        return { reference, providerRef, status: "completed" };
      case "checkout.session.async_payment_failed":
      case "checkout.session.expired":
        return { reference, providerRef, status: "failed" };
      default:
        return null; // Acknowledged, but nothing to record.
    }
  }
}

/**
 * Stripe signs `${timestamp}.${rawBody}` with HMAC-SHA256 and sends it as
 * `t=...,v1=...`. Any of the v1 signatures may match (Stripe sends several
 * during a secret rotation). Timestamps outside the tolerance are rejected so
 * a captured payload cannot be replayed later.
 */
export function verifyStripeSignature(
  rawBody: string,
  header: string | null,
  secret: string,
  toleranceSeconds = 300,
  now = Date.now(),
): boolean {
  if (!header) return false;

  let timestamp: string | null = null;
  const signatures: string[] = [];
  for (const part of header.split(",")) {
    const [key, value] = part.split("=", 2);
    if (key?.trim() === "t") timestamp = value?.trim() ?? null;
    if (key?.trim() === "v1" && value) signatures.push(value.trim());
  }
  if (!timestamp || signatures.length === 0) return false;

  const sentAt = Number(timestamp);
  if (!Number.isFinite(sentAt)) return false;
  if (Math.abs(now / 1000 - sentAt) > toleranceSeconds) return false;

  const expected = createHmac("sha256", secret).update(`${timestamp}.${rawBody}`).digest();
  return signatures.some((candidate) => {
    const given = Buffer.from(candidate, "hex");
    return given.length === expected.length && timingSafeEqual(given, expected);
  });
}
