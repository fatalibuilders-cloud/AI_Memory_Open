import {
  PaymentError,
  type CheckoutRequest,
  type CheckoutSession,
  type PaymentProvider,
  type SettlementEvent,
} from "./provider";

/**
 * M-Pesa via Safaricom's Daraja API (STK push / Lipa na M-Pesa Online).
 *
 * The shape of this rail differs from a card checkout in two ways that the
 * rest of the app has to accommodate:
 *
 *  1. There is no page to redirect to. We push a prompt to the donor's phone
 *     and they enter their PIN there, so `checkoutUrl` points at an in-app
 *     waiting page that watches the donation's status.
 *  2. The callback is not signed. Daraja posts a plain JSON body, so a
 *     settlement is only ever accepted when its CheckoutRequestID matches a
 *     donation we are already waiting on — an unsolicited callback carrying an
 *     unknown id settles nothing. Restrict the callback URL to Safaricom's
 *     published ranges at the edge as well; the application cannot verify
 *     origin on its own.
 *
 * Amounts are whole shillings: Daraja rejects decimals.
 */
export class MpesaProvider implements PaymentProvider {
  readonly name = "mpesa";
  readonly liveMode = true;

  private token: { value: string; expiresAt: number } | null = null;

  constructor(
    private readonly config: {
      consumerKey: string;
      consumerSecret: string;
      shortcode: string;
      passkey: string;
      callbackUrl: string;
      /** "paybill" pays to a business number, "till" to a buy-goods number. */
      shortcodeType?: "paybill" | "till";
    },
    private readonly apiBase = process.env.MPESA_ENV === "production"
      ? "https://api.safaricom.co.ke"
      : "https://sandbox.safaricom.co.ke",
  ) {}

  async createCheckout(request: CheckoutRequest): Promise<CheckoutSession> {
    if (request.frequency === "monthly") {
      // Daraja has no recurring mandate; a standing order would need the donor
      // to authorise each month. Better to say so than to silently take one
      // payment and call it monthly.
      throw new PaymentError(
        "Monthly giving is not available over M-Pesa yet — choose 'Give once', or give monthly by card.",
        400,
      );
    }
    if (!request.phone) {
      throw new PaymentError("Enter the M-Pesa number to send the prompt to.", 400);
    }
    if (request.currency !== "KES") {
      throw new PaymentError("M-Pesa donations are charged in Kenyan shillings.", 400);
    }

    const shillings = Math.round(request.amountCents / 100);
    if (shillings < 1) {
      throw new PaymentError("The smallest M-Pesa donation is one shilling.", 400);
    }

    const timestamp = stkTimestamp();
    const body = {
      BusinessShortCode: this.config.shortcode,
      Password: Buffer.from(`${this.config.shortcode}${this.config.passkey}${timestamp}`).toString(
        "base64",
      ),
      Timestamp: timestamp,
      TransactionType:
        this.config.shortcodeType === "till"
          ? "CustomerBuyGoodsOnline"
          : "CustomerPayBillOnline",
      Amount: shillings,
      PartyA: request.phone,
      PartyB: this.config.shortcode,
      PhoneNumber: request.phone,
      CallBackURL: this.config.callbackUrl,
      // Both appear on the donor's M-Pesa message, so the reference they can
      // quote to us is the one they already have in their SMS.
      AccountReference: request.reference,
      TransactionDesc: request.description.slice(0, 13),
    };

    const res = await fetch(`${this.apiBase}/mpesa/stkpush/v1/processrequest`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${await this.accessToken()}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    const payload = (await res.json().catch(() => ({}))) as {
      CheckoutRequestID?: string;
      ResponseCode?: string;
      errorMessage?: string;
      ResponseDescription?: string;
    };

    if (!res.ok || payload.ResponseCode !== "0" || !payload.CheckoutRequestID) {
      throw new PaymentError(
        friendlyMpesaError(payload.errorMessage ?? payload.ResponseDescription),
        502,
      );
    }

    return {
      checkoutUrl: `/donate/mpesa/${encodeURIComponent(request.reference)}`,
      providerRef: payload.CheckoutRequestID,
    };
  }

  async parseWebhook(rawBody: string): Promise<SettlementEvent | null> {
    return parseStkCallback(rawBody);
  }

  async cancelSubscription(): Promise<void> {
    // No recurring mandates on this rail; createCheckout refuses monthly gifts.
  }

  /** Daraja tokens last an hour; re-use one until it is nearly spent. */
  private async accessToken(): Promise<string> {
    if (this.token && this.token.expiresAt > Date.now()) return this.token.value;

    const basic = Buffer.from(
      `${this.config.consumerKey}:${this.config.consumerSecret}`,
    ).toString("base64");
    const res = await fetch(
      `${this.apiBase}/oauth/v1/generate?grant_type=client_credentials`,
      { headers: { Authorization: `Basic ${basic}` } },
    );

    const payload = (await res.json().catch(() => ({}))) as {
      access_token?: string;
      expires_in?: string | number;
    };
    if (!res.ok || !payload.access_token) {
      throw new PaymentError("Could not reach M-Pesa. Please try again in a moment.", 502);
    }

    const lifetime = Number(payload.expires_in ?? 3599) * 1000;
    this.token = {
      value: payload.access_token,
      expiresAt: Date.now() + Math.max(0, lifetime - 60_000),
    };
    return this.token.value;
  }
}

/**
 * Read an STK callback. Exported because the built-in simulator answers the
 * same endpoint with the same payload shape, so the callback route can be
 * rehearsed before Daraja credentials exist.
 */
export function parseStkCallback(rawBody: string): SettlementEvent | null {
  const event = JSON.parse(rawBody) as {
    Body?: {
      stkCallback?: {
        CheckoutRequestID?: string;
        ResultCode?: number | string;
        CallbackMetadata?: { Item?: { Name?: string; Value?: string | number }[] };
      };
    };
  };

  const callback = event.Body?.stkCallback;
  if (!callback?.CheckoutRequestID) return null;

  const code = Number(callback.ResultCode);
  // 0 is success. 1032 is the donor cancelling at the PIN prompt, 1037 a
  // timeout — both are ordinary failures, not errors on our side.
  const receipt = callback.CallbackMetadata?.Item?.find(
    (item) => item.Name === "MpesaReceiptNumber",
  )?.Value;

  return {
    reference: null, // Matched on the CheckoutRequestID we stored at push.
    providerRef: callback.CheckoutRequestID,
    externalRef: receipt ? String(receipt) : null,
    status: code === 0 ? "completed" : "failed",
  };
}

/** Daraja wants YYYYMMDDHHmmss in East Africa Time. */
export function stkTimestamp(now = new Date()): string {
  const eat = new Date(now.getTime() + 3 * 60 * 60 * 1000); // UTC+3, no DST
  const pad = (n: number) => String(n).padStart(2, "0");
  return (
    `${eat.getUTCFullYear()}${pad(eat.getUTCMonth() + 1)}${pad(eat.getUTCDate())}` +
    `${pad(eat.getUTCHours())}${pad(eat.getUTCMinutes())}${pad(eat.getUTCSeconds())}`
  );
}

/**
 * Normalise the many ways a Kenyan number gets typed — 0722…, +254722…,
 * 254722…, with spaces — into the 2547XXXXXXXX form Daraja requires.
 * Returns null when it is not a number M-Pesa can reach.
 */
export function normalizeMsisdn(input: string): string | null {
  const digits = input.replace(/[^\d]/g, "");
  const national = digits.startsWith("254")
    ? digits.slice(3)
    : digits.startsWith("0")
      ? digits.slice(1)
      : digits;
  // Kenyan mobile numbers are nine digits and begin 7 (Safaricom, Airtel) or 1.
  if (!/^[71]\d{8}$/.test(national)) return null;
  return `254${national}`;
}

function friendlyMpesaError(message: string | undefined): string {
  if (!message) return "M-Pesa could not start this payment. Please try again.";
  if (/subscriber|invalid.*msisdn/i.test(message)) {
    return "That number was not recognised by M-Pesa. Check it and try again.";
  }
  if (/insufficient/i.test(message)) return "There were not enough funds in that M-Pesa account.";
  return "M-Pesa could not start this payment. Please try again.";
}
