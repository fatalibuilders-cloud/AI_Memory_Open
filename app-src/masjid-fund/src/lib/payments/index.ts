import { MockProvider } from "./mock";
import { StripeProvider } from "./stripe";
import type { PaymentProvider } from "./provider";

export * from "./provider";

let provider: PaymentProvider | null = null;

/**
 * Stripe when STRIPE_SECRET_KEY is present, otherwise the built-in simulator.
 * Resolved once per process so the choice cannot change mid-flow.
 */
export function getPaymentProvider(): PaymentProvider {
  if (!provider) {
    const key = process.env.STRIPE_SECRET_KEY;
    provider = key
      ? new StripeProvider(key, process.env.STRIPE_WEBHOOK_SECRET)
      : new MockProvider();
  }
  return provider;
}

/** Test-only: forget the resolved provider so env changes take effect. */
export function resetPaymentProviderForTests(): void {
  provider = null;
}

/** Absolute base URL for provider redirects. */
export function appUrl(): string {
  return (process.env.APP_URL ?? "http://localhost:3000").replace(/\/$/, "");
}
