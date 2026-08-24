import {
  PaymentError,
  type CheckoutRequest,
  type CheckoutSession,
  type PaymentProvider,
  type SettlementEvent,
} from "./provider";

/**
 * PayPal via the Orders v2 REST API — no SDK, matching the Stripe adapter.
 *
 * PayPal splits payment into two steps: the donor approves an order on
 * PayPal's site, then the money is captured. We capture as soon as they come
 * back, and the webhook is the safety net for a donor who approves and then
 * closes the tab. Capture is idempotent here: PayPal answering
 * "already captured" is treated as success, not as an error.
 */
export class PayPalProvider implements PaymentProvider {
  readonly name = "paypal";
  readonly liveMode = true;

  private token: { value: string; expiresAt: number } | null = null;

  constructor(
    private readonly config: {
      clientId: string;
      clientSecret: string;
      /** Needed to verify webhook signatures; without it webhooks are refused. */
      webhookId?: string;
      returnUrl: string;
      cancelUrl: string;
    },
    private readonly apiBase = process.env.PAYPAL_ENV === "production"
      ? "https://api-m.paypal.com"
      : "https://api-m.sandbox.paypal.com",
  ) {}

  async createCheckout(request: CheckoutRequest): Promise<CheckoutSession> {
    if (request.frequency === "monthly") {
      // Recurring PayPal needs a product and billing plan created up front, and
      // a different approval flow. Until that exists, say so rather than taking
      // a single payment and calling it monthly.
      throw new PaymentError(
        "Monthly giving is not available through PayPal yet — choose 'Give once', or give monthly by card.",
        400,
      );
    }

    const order = await this.call<{
      id?: string;
      links?: { rel?: string; href?: string }[];
    }>("/v2/checkout/orders", {
      method: "POST",
      headers: { "PayPal-Request-Id": request.reference },
      body: {
        intent: "CAPTURE",
        purchase_units: [
          {
            // Comes back on the webhook and in PayPal's reporting, so a gift can
            // always be traced to its donation.
            custom_id: request.reference,
            description: request.description.slice(0, 127),
            amount: {
              currency_code: request.currency,
              value: (request.amountCents / 100).toFixed(2),
            },
          },
        ],
        payment_source: {
          paypal: {
            experience_context: {
              // Back through our own route, which captures the money before
              // showing the donor a receipt. PayPal appends ?token=<order id>.
              return_url: `${this.config.returnUrl}?ref=${encodeURIComponent(request.reference)}`,
              cancel_url: request.cancelUrl,
              user_action: "PAY_NOW",
              shipping_preference: "NO_SHIPPING",
            },
          },
        },
      },
    });

    const approve = order.links?.find(
      (link) => link.rel === "payer-action" || link.rel === "approve",
    )?.href;
    if (!order.id || !approve) {
      throw new PaymentError("PayPal could not start this donation. Please try again.", 502);
    }
    return { checkoutUrl: approve, providerRef: order.id };
  }

  /** Take the money for an approved order. Safe to call twice. */
  async capture(orderId: string): Promise<SettlementEvent | null> {
    try {
      const result = await this.call<{
        status?: string;
        purchase_units?: {
          custom_id?: string;
          payments?: { captures?: { id?: string; status?: string; custom_id?: string }[] };
        }[];
      }>(`/v2/checkout/orders/${encodeURIComponent(orderId)}/capture`, {
        method: "POST",
        headers: { "PayPal-Request-Id": `capture-${orderId}` },
        body: {},
      });

      const unit = result.purchase_units?.[0];
      const capture = unit?.payments?.captures?.[0];
      return {
        reference: unit?.custom_id ?? capture?.custom_id ?? null,
        providerRef: orderId,
        externalRef: capture?.id ?? null,
        status: result.status === "COMPLETED" ? "completed" : "failed",
      };
    } catch (err) {
      if (err instanceof PaymentError && err.message === "ORDER_ALREADY_CAPTURED") {
        // The webhook beat the donor's browser back. Nothing left to do.
        return null;
      }
      throw err;
    }
  }

  /**
   * PayPal signs webhooks with a certificate chain rather than an HMAC, so the
   * only sound way to verify one is to ask PayPal. Without a webhook id
   * configured we cannot verify, and an unverifiable payment instruction is
   * refused rather than trusted.
   */
  async parseWebhook(rawBody: string, headers: Headers): Promise<SettlementEvent | null> {
    if (!this.config.webhookId) {
      throw new PaymentError("PayPal webhook id is not configured", 500);
    }

    const verification = await this.call<{ verification_status?: string }>(
      "/v1/notifications/verify-webhook-signature",
      {
        method: "POST",
        body: {
          auth_algo: headers.get("paypal-auth-algo"),
          cert_url: headers.get("paypal-cert-url"),
          transmission_id: headers.get("paypal-transmission-id"),
          transmission_sig: headers.get("paypal-transmission-sig"),
          transmission_time: headers.get("paypal-transmission-time"),
          webhook_id: this.config.webhookId,
          webhook_event: JSON.parse(rawBody),
        },
      },
    );
    if (verification.verification_status !== "SUCCESS") {
      throw new PaymentError("Signature verification failed", 400);
    }

    const event = JSON.parse(rawBody) as {
      event_type?: string;
      resource?: {
        id?: string;
        custom_id?: string;
        supplementary_data?: { related_ids?: { order_id?: string } };
        purchase_units?: { custom_id?: string }[];
      };
    };
    const resource = event.resource ?? {};
    const reference = resource.custom_id ?? resource.purchase_units?.[0]?.custom_id ?? null;
    const orderId = resource.supplementary_data?.related_ids?.order_id ?? null;

    switch (event.event_type) {
      case "PAYMENT.CAPTURE.COMPLETED":
        return {
          reference,
          providerRef: orderId,
          externalRef: resource.id ?? null,
          status: "completed",
        };
      case "PAYMENT.CAPTURE.DENIED":
      case "PAYMENT.CAPTURE.REVERSED":
        return { reference, providerRef: orderId, status: "failed" };
      case "CHECKOUT.ORDER.APPROVED":
        // Approval is not money. The capture on return does that; if the donor
        // never comes back, PAYMENT.CAPTURE.COMPLETED will.
        if (resource.id) await this.capture(resource.id);
        return null;
      default:
        return null;
    }
  }

  async cancelSubscription(): Promise<void> {
    // No recurring agreements on this rail; createCheckout refuses monthly gifts.
  }

  private async call<T>(
    path: string,
    init: { method?: string; headers?: Record<string, string>; body?: unknown },
  ): Promise<T> {
    const res = await fetch(`${this.apiBase}${path}`, {
      method: init.method ?? "GET",
      headers: {
        Authorization: `Bearer ${await this.accessToken()}`,
        "Content-Type": "application/json",
        ...(init.headers ?? {}),
      },
      body: init.body === undefined ? undefined : JSON.stringify(init.body),
    });

    const payload = (await res.json().catch(() => ({}))) as {
      name?: string;
      message?: string;
      details?: { issue?: string; description?: string }[];
    };
    if (!res.ok) {
      const issue = payload.details?.[0]?.issue;
      if (issue === "ORDER_ALREADY_CAPTURED") throw new PaymentError("ORDER_ALREADY_CAPTURED", 409);
      throw new PaymentError(
        payload.details?.[0]?.description ?? payload.message ?? "PayPal rejected the request.",
        502,
      );
    }
    return payload as T;
  }

  /** PayPal tokens last hours; keep one until it is nearly spent. */
  private async accessToken(): Promise<string> {
    if (this.token && this.token.expiresAt > Date.now()) return this.token.value;

    const basic = Buffer.from(`${this.config.clientId}:${this.config.clientSecret}`).toString(
      "base64",
    );
    const res = await fetch(`${this.apiBase}/v1/oauth2/token`, {
      method: "POST",
      headers: {
        Authorization: `Basic ${basic}`,
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: "grant_type=client_credentials",
    });

    const payload = (await res.json().catch(() => ({}))) as {
      access_token?: string;
      expires_in?: number;
    };
    if (!res.ok || !payload.access_token) {
      throw new PaymentError("Could not reach PayPal. Please try again in a moment.", 502);
    }

    this.token = {
      value: payload.access_token,
      expiresAt: Date.now() + Math.max(0, (payload.expires_in ?? 3600) * 1000 - 60_000),
    };
    return this.token.value;
  }
}
