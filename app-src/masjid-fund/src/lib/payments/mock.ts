import type {
  CheckoutRequest,
  CheckoutSession,
  PaymentProvider,
  SettlementEvent,
} from "./provider";

/**
 * Built-in simulator used whenever no real provider is configured. It sends
 * the donor to an in-app page that mimics a hosted checkout, so the whole
 * donation flow — including receipts and project totals — is exercisable
 * without keys. No money moves.
 */
export class MockProvider implements PaymentProvider {
  readonly name = "mock";
  readonly liveMode = false;

  async createCheckout(request: CheckoutRequest): Promise<CheckoutSession> {
    return {
      checkoutUrl: `/checkout/${encodeURIComponent(request.reference)}`,
      providerRef: `mock_${request.reference}`,
    };
  }

  async parseWebhook(rawBody: string): Promise<SettlementEvent | null> {
    const payload = JSON.parse(rawBody) as {
      reference?: string;
      status?: string;
      providerRef?: string;
    };
    if (payload.status !== "completed" && payload.status !== "failed") return null;
    return {
      reference: payload.reference ?? null,
      providerRef: payload.providerRef ?? null,
      status: payload.status,
    };
  }
}
