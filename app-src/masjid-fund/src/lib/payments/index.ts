import { BankTransferProvider, bankDetails } from "./bank";
import { MockProvider } from "./mock";
import { MpesaProvider } from "./mpesa";
import { PayPalProvider } from "./paypal";
import { StripeProvider } from "./stripe";
import type { PaymentProvider } from "./provider";

export * from "./provider";
export { bankDetails } from "./bank";

/**
 * Which rail handles a donation.
 *
 * Each method resolves to a real provider when its keys are present, and to the
 * built-in simulator when they are not — so a half-configured deployment still
 * works end to end, and the UI can say plainly which rails are live. Bank
 * transfer is the exception: with no account details there is nothing to
 * simulate, so the rail is simply not offered.
 */
export const PAYMENT_METHODS = ["card", "mpesa", "paypal", "bank"] as const;
export type PaymentMethod = (typeof PAYMENT_METHODS)[number];

export const METHOD_LABELS: Record<PaymentMethod, string> = {
  card: "Card",
  mpesa: "M-Pesa",
  paypal: "PayPal",
  bank: "Bank transfer",
};

export const METHOD_HINTS: Record<PaymentMethod, string> = {
  card: "Visa, Mastercard, Apple Pay",
  mpesa: "Pay from your phone in shillings",
  paypal: "Pay with your PayPal balance or card",
  bank: "Transfer yourself, quoting a reference",
};

/** The currency each rail charges in. */
export const METHOD_CURRENCY: Record<PaymentMethod, "USD" | "KES"> = {
  card: "USD",
  mpesa: "KES",
  paypal: "USD",
  bank: "USD",
};

/** Rails that cannot take a recurring gift, so the form does not offer them for one. */
export const METHODS_WITHOUT_RECURRING: PaymentMethod[] = ["mpesa", "paypal", "bank"];

const providers = new Map<PaymentMethod, PaymentProvider>();

export function getPaymentProvider(method: PaymentMethod = "card"): PaymentProvider {
  const existing = providers.get(method);
  if (existing) return existing;

  const provider = build(method);
  providers.set(method, provider);
  return provider;
}

function build(method: PaymentMethod): PaymentProvider {
  if (method === "bank") return new BankTransferProvider();

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

  if (method === "paypal") {
    const { PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET } = process.env;
    if (PAYPAL_CLIENT_ID && PAYPAL_CLIENT_SECRET) {
      return new PayPalProvider({
        clientId: PAYPAL_CLIENT_ID,
        clientSecret: PAYPAL_CLIENT_SECRET,
        webhookId: process.env.PAYPAL_WEBHOOK_ID,
        returnUrl: `${appUrl()}/api/payments/paypal/return`,
        cancelUrl: `${appUrl()}/donate`,
      });
    }
    return new MockProvider("paypal");
  }

  const key = process.env.STRIPE_SECRET_KEY;
  return key
    ? new StripeProvider(key, process.env.STRIPE_WEBHOOK_SECRET)
    : new MockProvider("card");
}

/** Rails a donor can actually choose on this deployment. */
export function availableMethods(): PaymentMethod[] {
  return PAYMENT_METHODS.filter((method) => method !== "bank" || bankDetails() !== null);
}

/** True when at least one rail moves real money. */
export function anyLiveMethod(): boolean {
  return availableMethods().some(
    (method) => method !== "bank" && getPaymentProvider(method).liveMode,
  );
}

/** Test-only: forget resolved providers so env changes take effect. */
export function resetPaymentProviderForTests(): void {
  providers.clear();
}

/** Absolute base URL for provider redirects and callbacks. */
export function appUrl(): string {
  return (process.env.APP_URL ?? "http://localhost:3000").replace(/\/$/, "");
}
