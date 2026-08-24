import { parseStkCallback } from "./mpesa";
import type {
  CheckoutRequest,
  CheckoutSession,
  PaymentProvider,
  SettlementEvent,
} from "./provider";

/**
 * Built-in simulator, used for any rail that has no credentials configured. It
 * sends the donor to an in-app page that mimics that rail's checkout, so the
 * whole donation flow — including receipts, totals and the failure path — is
 * exercisable without keys. No money moves.
 */
export class MockProvider implements PaymentProvider {
  readonly liveMode = false;
  readonly name: string;

  constructor(private readonly method: "card" | "mpesa" | "paypal" = "card") {
    // Recorded on the donation so the ledger shows which rail was simulated.
    this.name = method === "card" ? "mock" : `mock_${method}`;
  }

  async createCheckout(request: CheckoutRequest): Promise<CheckoutSession> {
    const reference = encodeURIComponent(request.reference);
    return {
      checkoutUrl:
        this.method === "mpesa" ? `/donate/mpesa/${reference}` : `/checkout/${reference}`,
      providerRef: `mock_${request.reference}`,
    };
  }

  async parseWebhook(rawBody: string): Promise<SettlementEvent | null> {
    // Standing in for M-Pesa means answering M-Pesa's callback shape, so the
    // real payload can be rehearsed against the real endpoint.
    if (this.method === "mpesa") return parseStkCallback(rawBody);

    const payload = JSON.parse(rawBody) as {
      reference?: string;
      status?: string;
      providerRef?: string;
    };
    if (payload.status !== "completed" && payload.status !== "failed") return null;
    return {
      reference: payload.reference ?? null,
      providerRef: payload.providerRef ?? null,
      subscriptionRef: payload.reference ? `mock_sub_${payload.reference}` : null,
      status: payload.status,
    };
  }

  async cancelSubscription(): Promise<void> {
    // Nothing to call — the donation row is marked cancelled by the caller.
  }
}
