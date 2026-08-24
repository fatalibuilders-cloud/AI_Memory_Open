import { describe, expect, it } from "vitest";
import { PayPalProvider } from "./paypal";
import { PaymentError } from "./provider";

const config = {
  clientId: "client",
  clientSecret: "secret",
  webhookId: "WH-123",
  returnUrl: "https://example.org/api/payments/paypal/return",
  cancelUrl: "https://example.org/donate",
};

const request = {
  reference: "MF-TEST1234",
  amountCents: 5000,
  currency: "USD",
  frequency: "one_time" as const,
  description: "Masjid al-Noor — Sadaqah Jariyah",
  donorEmail: "donor@example.com",
  successUrl: "https://example.org/donate/thank-you?ref=MF-TEST1234",
  cancelUrl: "https://example.org/donate",
};

/** Answers the OAuth call, then whatever each test needs, capturing requests. */
function stubPayPal(responses: { status?: number; body: unknown }[]) {
  const calls: { url: string; body: Record<string, unknown> }[] = [];
  let next = 0;
  globalThis.fetch = (async (url: string, init: RequestInit = {}) => {
    if (String(url).includes("/v1/oauth2/token")) {
      return { ok: true, json: async () => ({ access_token: "tok", expires_in: 3600 }) } as Response;
    }
    calls.push({
      url: String(url),
      body: init.body ? JSON.parse(String(init.body)) : {},
    });
    const response = responses[Math.min(next++, responses.length - 1)];
    return {
      ok: (response.status ?? 200) < 400,
      json: async () => response.body,
    } as Response;
  }) as unknown as typeof fetch;
  return calls;
}

describe("PayPalProvider.createCheckout", () => {
  it("creates an order and returns PayPal's approval link", async () => {
    const calls = stubPayPal([
      {
        body: {
          id: "5O190127TN364715T",
          links: [
            { rel: "self", href: "https://api-m.sandbox.paypal.com/v2/checkout/orders/5O19" },
            { rel: "payer-action", href: "https://www.sandbox.paypal.com/checkoutnow?token=5O19" },
          ],
        },
      },
    ]);

    const session = await new PayPalProvider(config).createCheckout(request);
    expect(session).toEqual({
      checkoutUrl: "https://www.sandbox.paypal.com/checkoutnow?token=5O19",
      providerRef: "5O190127TN364715T",
    });

    const unit = (calls[0].body.purchase_units as Record<string, unknown>[])[0];
    expect(calls[0].body.intent).toBe("CAPTURE");
    expect(unit.custom_id).toBe("MF-TEST1234");
    expect(unit.amount).toEqual({ currency_code: "USD", value: "50.00" });
  });

  it("returns the donor through our capture route, not straight to the receipt", async () => {
    const calls = stubPayPal([
      { body: { id: "o1", links: [{ rel: "payer-action", href: "https://paypal.test/pay" }] } },
    ]);
    await new PayPalProvider(config).createCheckout(request);

    const source = calls[0].body.payment_source as {
      paypal: { experience_context: { return_url: string } };
    };
    expect(source.paypal.experience_context.return_url).toBe(
      "https://example.org/api/payments/paypal/return?ref=MF-TEST1234",
    );
  });

  it("refuses monthly giving rather than taking a single payment", async () => {
    stubPayPal([{ body: { id: "o1", links: [] } }]);
    await expect(
      new PayPalProvider(config).createCheckout({ ...request, frequency: "monthly" }),
    ).rejects.toBeInstanceOf(PaymentError);
  });

  it("fails loudly when PayPal returns no approval link", async () => {
    stubPayPal([{ body: { id: "o1", links: [{ rel: "self", href: "…" }] } }]);
    await expect(new PayPalProvider(config).createCheckout(request)).rejects.toBeInstanceOf(
      PaymentError,
    );
  });
});

describe("PayPalProvider.capture", () => {
  it("reports a completed capture with the donation reference", async () => {
    stubPayPal([
      {
        body: {
          status: "COMPLETED",
          purchase_units: [
            {
              custom_id: "MF-TEST1234",
              payments: { captures: [{ id: "3C679366HH908993F", status: "COMPLETED" }] },
            },
          ],
        },
      },
    ]);

    expect(await new PayPalProvider(config).capture("5O19")).toEqual({
      reference: "MF-TEST1234",
      providerRef: "5O19",
      externalRef: "3C679366HH908993F",
      status: "completed",
    });
  });

  it("treats an already-captured order as nothing left to do", async () => {
    stubPayPal([
      { status: 422, body: { details: [{ issue: "ORDER_ALREADY_CAPTURED" }] } },
    ]);
    // The webhook got there first; capturing again must not error the donor's return.
    expect(await new PayPalProvider(config).capture("5O19")).toBeNull();
  });

  it("surfaces other failures rather than silently swallowing them", async () => {
    stubPayPal([
      { status: 422, body: { details: [{ issue: "INSTRUMENT_DECLINED", description: "Declined" }] } },
    ]);
    await expect(new PayPalProvider(config).capture("5O19")).rejects.toBeInstanceOf(PaymentError);
  });
});

describe("PayPalProvider.parseWebhook", () => {
  const headers = new Headers({
    "paypal-auth-algo": "SHA256withRSA",
    "paypal-cert-url": "https://api.sandbox.paypal.com/cert.pem",
    "paypal-transmission-id": "t-1",
    "paypal-transmission-sig": "sig",
    "paypal-transmission-time": "2026-08-22T10:00:00Z",
  });

  const captureCompleted = JSON.stringify({
    event_type: "PAYMENT.CAPTURE.COMPLETED",
    resource: {
      id: "3C679366HH908993F",
      custom_id: "MF-TEST1234",
      supplementary_data: { related_ids: { order_id: "5O19" } },
    },
  });

  it("acts on a verified capture", async () => {
    stubPayPal([{ body: { verification_status: "SUCCESS" } }]);
    const event = await new PayPalProvider(config).parseWebhook(captureCompleted, headers);
    expect(event).toEqual({
      reference: "MF-TEST1234",
      providerRef: "5O19",
      externalRef: "3C679366HH908993F",
      status: "completed",
    });
  });

  it("refuses a payload PayPal will not vouch for", async () => {
    stubPayPal([{ body: { verification_status: "FAILURE" } }]);
    await expect(
      new PayPalProvider(config).parseWebhook(captureCompleted, headers),
    ).rejects.toBeInstanceOf(PaymentError);
  });

  it("refuses webhooks entirely when no webhook id is configured", async () => {
    stubPayPal([{ body: {} }]);
    await expect(
      new PayPalProvider({ ...config, webhookId: undefined }).parseWebhook(captureCompleted, headers),
    ).rejects.toMatchObject({ status: 500 });
  });

  it("marks a denied capture as failed", async () => {
    stubPayPal([{ body: { verification_status: "SUCCESS" } }]);
    const denied = JSON.stringify({
      event_type: "PAYMENT.CAPTURE.DENIED",
      resource: { id: "c1", custom_id: "MF-TEST1234" },
    });
    expect(await new PayPalProvider(config).parseWebhook(denied, headers)).toMatchObject({
      status: "failed",
    });
  });

  it("ignores event types that are not money moving", async () => {
    stubPayPal([{ body: { verification_status: "SUCCESS" } }]);
    const other = JSON.stringify({ event_type: "BILLING.PLAN.CREATED", resource: { id: "p1" } });
    expect(await new PayPalProvider(config).parseWebhook(other, headers)).toBeNull();
  });
});
