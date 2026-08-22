import { afterEach, describe, expect, it, vi } from "vitest";
import { PaymentError } from "./provider";
import { MpesaProvider, normalizeMsisdn, stkTimestamp } from "./mpesa";

const config = {
  consumerKey: "key",
  consumerSecret: "secret",
  shortcode: "174379",
  passkey: "passkey",
  callbackUrl: "https://example.org/api/payments/mpesa/callback",
};

const request = {
  reference: "MF-TEST1234",
  amountCents: 645000, // Ksh 6,450
  currency: "KES",
  frequency: "one_time" as const,
  description: "Masjid al-Noor — Sadaqah Jariyah",
  donorEmail: "donor@example.com",
  phone: "254722000000",
  successUrl: "https://example.org/donate/thank-you?ref=MF-TEST1234",
  cancelUrl: "https://example.org/donate",
};

/** Captures outgoing calls instead of reaching Safaricom. */
function stubDaraja(stkResponse: unknown, ok = true) {
  const calls: { url: string; body: Record<string, unknown> }[] = [];
  globalThis.fetch = (async (url: string, init: RequestInit = {}) => {
    if (String(url).includes("/oauth/")) {
      return {
        ok: true,
        json: async () => ({ access_token: "tok_abc", expires_in: "3599" }),
      } as Response;
    }
    calls.push({ url: String(url), body: JSON.parse(String(init.body)) });
    return { ok, json: async () => stkResponse } as Response;
  }) as unknown as typeof fetch;
  return calls;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("normalizeMsisdn", () => {
  it("accepts the ways a Kenyan number is actually typed", () => {
    for (const input of [
      "0722000000",
      "+254722000000",
      "254722000000",
      "0722 000 000",
      "+254 722 000 000",
    ]) {
      expect(normalizeMsisdn(input)).toBe("254722000000");
    }
    expect(normalizeMsisdn("0110000000")).toBe("254110000000"); // newer 01… range
  });

  it("rejects anything M-Pesa could not reach", () => {
    expect(normalizeMsisdn("")).toBeNull();
    expect(normalizeMsisdn("0722")).toBeNull(); // too short
    expect(normalizeMsisdn("07220000001")).toBeNull(); // too long
    expect(normalizeMsisdn("0202000000")).toBeNull(); // landline
    expect(normalizeMsisdn("not a phone")).toBeNull();
  });
});

describe("stkTimestamp", () => {
  it("is East Africa Time in the format Daraja expects", () => {
    // 21:30 UTC is 00:30 the next day in Nairobi.
    expect(stkTimestamp(new Date("2026-08-21T21:30:05Z"))).toBe("20260822003005");
    expect(stkTimestamp(new Date("2026-01-02T09:05:00Z"))).toBe("20260102120500");
  });
});

describe("MpesaProvider.createCheckout", () => {
  it("pushes whole shillings and sends the donor to the waiting page", async () => {
    const calls = stubDaraja({ ResponseCode: "0", CheckoutRequestID: "ws_CO_123" });
    const session = await new MpesaProvider(config).createCheckout(request);

    expect(session).toEqual({
      checkoutUrl: "/donate/mpesa/MF-TEST1234",
      providerRef: "ws_CO_123",
    });
    expect(calls[0].body.Amount).toBe(6450);
    expect(calls[0].body.PhoneNumber).toBe("254722000000");
    expect(calls[0].body.AccountReference).toBe("MF-TEST1234");
    expect(calls[0].body.TransactionType).toBe("CustomerPayBillOnline");
    expect(calls[0].body.CallBackURL).toBe(config.callbackUrl);
  });

  it("uses the buy-goods transaction type for a till number", async () => {
    const calls = stubDaraja({ ResponseCode: "0", CheckoutRequestID: "ws_CO_9" });
    await new MpesaProvider({ ...config, shortcodeType: "till" }).createCheckout(request);
    expect(calls[0].body.TransactionType).toBe("CustomerBuyGoodsOnline");
  });

  it("refuses monthly giving rather than taking one payment and calling it monthly", async () => {
    stubDaraja({ ResponseCode: "0", CheckoutRequestID: "ws_CO_1" });
    await expect(
      new MpesaProvider(config).createCheckout({ ...request, frequency: "monthly" }),
    ).rejects.toBeInstanceOf(PaymentError);
  });

  it("refuses a missing phone number and a non-KES amount", async () => {
    stubDaraja({ ResponseCode: "0", CheckoutRequestID: "ws_CO_1" });
    const provider = new MpesaProvider(config);
    await expect(provider.createCheckout({ ...request, phone: null })).rejects.toBeInstanceOf(
      PaymentError,
    );
    await expect(provider.createCheckout({ ...request, currency: "USD" })).rejects.toBeInstanceOf(
      PaymentError,
    );
  });

  it("turns a Daraja rejection into something a donor can act on", async () => {
    stubDaraja({ errorMessage: "Invalid MSISDN" }, false);
    await expect(new MpesaProvider(config).createCheckout(request)).rejects.toMatchObject({
      status: 502,
      message: expect.stringContaining("not recognised"),
    });
  });

  it("reuses the access token across pushes", async () => {
    let oauthCalls = 0;
    globalThis.fetch = (async (url: string) => {
      if (String(url).includes("/oauth/")) {
        oauthCalls += 1;
        return { ok: true, json: async () => ({ access_token: "t", expires_in: "3599" }) } as Response;
      }
      return {
        ok: true,
        json: async () => ({ ResponseCode: "0", CheckoutRequestID: "ws_CO_x" }),
      } as Response;
    }) as unknown as typeof fetch;

    const provider = new MpesaProvider(config);
    await provider.createCheckout(request);
    await provider.createCheckout({ ...request, reference: "MF-SECOND01" });
    expect(oauthCalls).toBe(1);
  });
});

describe("MpesaProvider.parseWebhook", () => {
  const provider = new MpesaProvider(config);

  function callback(resultCode: number, receipt?: string) {
    return JSON.stringify({
      Body: {
        stkCallback: {
          MerchantRequestID: "m-1",
          CheckoutRequestID: "ws_CO_123",
          ResultCode: resultCode,
          ResultDesc: "…",
          ...(receipt
            ? { CallbackMetadata: { Item: [{ Name: "MpesaReceiptNumber", Value: receipt }] } }
            : {}),
        },
      },
    });
  }

  it("reads a success, keeping the donor's M-Pesa code", async () => {
    const event = await provider.parseWebhook(callback(0, "SFI4X8YZ01"));
    expect(event).toEqual({
      reference: null,
      providerRef: "ws_CO_123",
      externalRef: "SFI4X8YZ01",
      status: "completed",
    });
  });

  it("treats a cancelled prompt and a timeout as ordinary failures", async () => {
    for (const code of [1032, 1037, 1]) {
      const event = await provider.parseWebhook(callback(code));
      expect(event).toMatchObject({ status: "failed", providerRef: "ws_CO_123" });
    }
  });

  it("ignores a payload with no callback in it", async () => {
    expect(await provider.parseWebhook(JSON.stringify({ Body: {} }))).toBeNull();
  });

  it("never carries a donation reference from the payload", async () => {
    // The callback is unsigned, so the only thing trusted is the id we issued.
    const spoofed = JSON.stringify({
      Body: {
        stkCallback: {
          CheckoutRequestID: "ws_CO_123",
          ResultCode: 0,
          CallbackMetadata: { Item: [{ Name: "AccountReference", Value: "MF-SOMEONEELSE" }] },
        },
      },
    });
    const event = await provider.parseWebhook(spoofed);
    expect(event?.reference).toBeNull();
  });
});
