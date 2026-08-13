import { createHmac } from "crypto";
import { describe, expect, it } from "vitest";
import { PaymentError } from "./provider";
import { StripeProvider, verifyStripeSignature } from "./stripe";

const SECRET = "whsec_test_secret";

function sign(body: string, secret = SECRET, timestamp = Math.floor(Date.now() / 1000)) {
  const signature = createHmac("sha256", secret).update(`${timestamp}.${body}`).digest("hex");
  return `t=${timestamp},v1=${signature}`;
}

describe("verifyStripeSignature", () => {
  const body = JSON.stringify({ id: "evt_1" });

  it("accepts a correctly signed payload", () => {
    expect(verifyStripeSignature(body, sign(body), SECRET)).toBe(true);
  });

  it("accepts a payload during a secret rotation (several v1 signatures)", () => {
    const timestamp = Math.floor(Date.now() / 1000);
    const good = sign(body, SECRET, timestamp).split("v1=")[1];
    const header = `t=${timestamp},v1=${"0".repeat(64)},v1=${good}`;
    expect(verifyStripeSignature(body, header, SECRET)).toBe(true);
  });

  it("rejects a tampered body, a wrong secret and a missing header", () => {
    const header = sign(body);
    expect(verifyStripeSignature(`${body} `, header, SECRET)).toBe(false);
    expect(verifyStripeSignature(body, header, "whsec_other")).toBe(false);
    expect(verifyStripeSignature(body, null, SECRET)).toBe(false);
    expect(verifyStripeSignature(body, "v1=deadbeef", SECRET)).toBe(false);
  });

  it("rejects a replayed payload outside the tolerance window", () => {
    const old = Math.floor(Date.now() / 1000) - 3600;
    expect(verifyStripeSignature(body, sign(body, SECRET, old), SECRET)).toBe(false);
  });
});

describe("StripeProvider.parseWebhook", () => {
  const provider = new StripeProvider("sk_test", SECRET);

  async function parse(event: unknown) {
    const body = JSON.stringify(event);
    return provider.parseWebhook(body, new Headers({ "stripe-signature": sign(body) }));
  }

  it("maps a completed checkout session to a settlement", async () => {
    const event = await parse({
      type: "checkout.session.completed",
      data: { object: { id: "cs_123", client_reference_id: "MF-ABCD1234" } },
    });
    expect(event).toEqual({
      reference: "MF-ABCD1234",
      providerRef: "cs_123",
      subscriptionRef: null,
      status: "completed",
    });
  });

  it("carries the subscription id through for a monthly gift", async () => {
    const event = await parse({
      type: "checkout.session.completed",
      data: {
        object: { id: "cs_m1", client_reference_id: "MF-MONTHLY1", subscription: "sub_9" },
      },
    });
    expect(event).toMatchObject({ subscriptionRef: "sub_9", status: "completed" });
  });

  it("falls back to the metadata reference", async () => {
    const event = await parse({
      type: "checkout.session.async_payment_failed",
      data: { object: { id: "cs_9", metadata: { reference: "MF-ZZZZ0000" } } },
    });
    expect(event).toMatchObject({ reference: "MF-ZZZZ0000", status: "failed" });
  });

  it("ignores event types we do not act on", async () => {
    expect(await parse({ type: "customer.created", data: { object: { id: "cus_1" } } })).toBeNull();
  });

  it("refuses a payload whose signature does not verify", async () => {
    await expect(
      provider.parseWebhook("{}", new Headers({ "stripe-signature": "t=1,v1=bad" })),
    ).rejects.toBeInstanceOf(PaymentError);
  });
});

describe("StripeProvider.createCheckout", () => {
  const request = {
    reference: "MF-TEST1234",
    amountCents: 5000,
    currency: "USD",
    description: "Masjid al-Noor — Sadaqah Jariyah",
    donorEmail: "donor@example.com",
    successUrl: "https://example.org/donate/thank-you?ref=MF-TEST1234",
    cancelUrl: "https://example.org/donate",
  };

  /** Captures the outgoing request instead of calling Stripe. */
  function stubFetch(response: unknown, ok = true) {
    const calls: { url: string; body: URLSearchParams }[] = [];
    const fetchStub = (async (url: string, init: RequestInit) => {
      calls.push({ url, body: new URLSearchParams(String(init.body)) });
      return { ok, json: async () => response } as Response;
    }) as unknown as typeof fetch;
    return { calls, fetchStub };
  }

  it("sends a one-time payment session and returns the hosted URL", async () => {
    const { calls, fetchStub } = stubFetch({ id: "cs_1", url: "https://checkout.stripe.com/c/1" });
    globalThis.fetch = fetchStub;

    const provider = new StripeProvider("sk_test", SECRET);
    const session = await provider.createCheckout({ ...request, frequency: "one_time" });

    expect(session).toEqual({ checkoutUrl: "https://checkout.stripe.com/c/1", providerRef: "cs_1" });
    expect(calls[0].body.get("mode")).toBe("payment");
    expect(calls[0].body.get("client_reference_id")).toBe("MF-TEST1234");
    expect(calls[0].body.get("line_items[0][price_data][unit_amount]")).toBe("5000");
    expect(calls[0].body.get("line_items[0][price_data][currency]")).toBe("usd");
  });

  it("sends a monthly gift as a subscription with a monthly interval", async () => {
    const { calls, fetchStub } = stubFetch({ id: "cs_2", url: "https://checkout.stripe.com/c/2" });
    globalThis.fetch = fetchStub;

    const provider = new StripeProvider("sk_test", SECRET);
    await provider.createCheckout({ ...request, frequency: "monthly" });

    expect(calls[0].body.get("mode")).toBe("subscription");
    expect(calls[0].body.get("line_items[0][price_data][recurring][interval]")).toBe("month");
  });

  it("surfaces a provider error as a PaymentError", async () => {
    const { fetchStub } = stubFetch({ error: { message: "Amount too small" } }, false);
    globalThis.fetch = fetchStub;

    const provider = new StripeProvider("sk_test", SECRET);
    await expect(
      provider.createCheckout({ ...request, frequency: "one_time" }),
    ).rejects.toBeInstanceOf(PaymentError);
  });
});
