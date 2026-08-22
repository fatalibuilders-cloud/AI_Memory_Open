import { MockProvider } from "./mock";
import { MpesaProvider } from "./mpesa";
import { StripeProvider } from "./stripe";
import type { PaymentProvider } from "./provider";

export * from "./provider";

/**
 * Which rail handles a donation.
 *
 * Each method resolves to a real provider when its keys are present, and to the
 * built-in simulator when they are not — so a half-configured deployment still
 * works end to end, and the UI can say plainly which rails are live.
 */
export const PAYMENT_METHODS = ["card", "mpesa"] as const;
export type PaymentMethod = (typeof PAYMENT_METHODS)[number];

export const METHOD_LABELS: Record<PaymentMethod, string> = {
  card: "Card",
  mpesa: "M-Pesa",
};

/** The currency each rail charges in. */
export const METHOD_CURRENCY: Record<PaymentMethod, "USD" | "KES"> = {
  card: "USD",
  mpesa: "KES",
};

const providers = new Map<PaymentMethod, PaymentProvider>();

export function getPaymentProvider(method: PaymentMethod = "card"): PaymentProvider {
  const existing = providers.get(method);
  if (existing) return existing;

  const provider = build(method);
  providers.set(method, provider);
  return provider;
}

function build(method: PaymentMethod): PaymentProvider {
  if (method === "mpesa") {
    const { MPESA_CONSUMER_KEY, MPESA_CONSUMER_SECRET, MPESA_SHORTCODE, MPESA_PASSKEY } =
      process.env;
    if (MPESA_CONSUMER_KEY && MPESA_CONSUMER_SECRET && MPESA_SHORTCODE && MPESA_PASSKEY) {
      return new MpesaProvider({
        consumerKey: MPESA_CONSUMER_KEY,
        consumerSecret: MPESA_CONSUMER_SECRET,
        shortcode: MPESA_SHORTCODE,
        passkey: MPESA_PASSKEY,
        callbackUrl: `${appUrl()}/api/payments/mpesa/callback`,
        shortcodeType: process.env.MPESA_SHORTCODE_TYPE === "till" ? "till" : "paybill",
      });
    }
    return new MockProvider("mpesa");
  }

  const key = process.env.STRIPE_SECRET_KEY;
  return key
    ? new StripeProvider(key, process.env.STRIPE_WEBHOOK_SECRET)
    : new MockProvider("card");
}

/** Which rails are actually configured, for the donate form and the dashboard. */
export function liveMethods(): PaymentMethod[] {
  return PAYMENT_METHODS.filter((method) => getPaymentProvider(method).liveMode);
}

/** Test-only: forget resolved providers so env changes take effect. */
export function resetPaymentProviderForTests(): void {
  providers.clear();
}

/** Absolute base URL for provider redirects and callbacks. */
export function appUrl(): string {
  return (process.env.APP_URL ?? "http://localhost:3000").replace(/\/$/, "");
}
