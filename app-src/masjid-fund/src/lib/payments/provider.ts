import type { Frequency } from "@/lib/donation";

/**
 * Payment provider boundary. The donation flow never talks to a payment API
 * directly — it asks the configured provider for a checkout URL and later
 * receives a settlement signal. Swapping Stripe for M-Pesa, PayPal or a bank
 * transfer reconciler means adding one file here.
 */

export interface CheckoutRequest {
  reference: string;
  amountCents: number;
  currency: string;
  frequency: Frequency;
  /** Line-item description shown on the provider's payment page. */
  description: string;
  donorEmail: string;
  /** Normalised MSISDN, for rails that push a prompt to a phone. */
  phone?: string | null;
  successUrl: string;
  cancelUrl: string;
}

export interface CheckoutSession {
  /** Where to send the donor to pay. */
  checkoutUrl: string;
  /** Provider's own identifier for the attempt, when it issues one up front. */
  providerRef: string | null;
}

export interface SettlementEvent {
  /** Our donation reference, recovered from the provider's payload. */
  reference: string | null;
  providerRef: string | null;
  /** Recurring-agreement id, present when a monthly gift starts. */
  subscriptionRef?: string | null;
  /** The donor's own receipt from the provider — an M-Pesa code, say. */
  externalRef?: string | null;
  status: "completed" | "failed";
}

export class PaymentError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

export interface PaymentProvider {
  readonly name: string;
  /** False for the built-in simulator — the UI labels test-mode payments. */
  readonly liveMode: boolean;
  createCheckout(request: CheckoutRequest): Promise<CheckoutSession>;
  /**
   * Verify and interpret a provider webhook. Returns null for events we do
   * not act on. Throws PaymentError when the signature does not verify.
   */
  parseWebhook(rawBody: string, headers: Headers): Promise<SettlementEvent | null>;
  /**
   * Stop a recurring agreement. Providers without recurring support, and the
   * simulator, simply resolve — the donation is still marked cancelled here.
   */
  cancelSubscription(subscriptionRef: string): Promise<void>;
}
