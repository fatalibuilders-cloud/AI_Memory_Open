import type {
  CheckoutRequest,
  CheckoutSession,
  PaymentProvider,
  SettlementEvent,
} from "./provider";

/**
 * Bank transfer and direct M-Pesa paybill: the rails where the money moves
 * entirely outside the site.
 *
 * There is no API to call and no callback to wait for. The donation is recorded
 * as pending with a reference for the donor to quote, they are shown where to
 * send it, and it settles when a member of staff matches it against the
 * statement in /admin/donations. That manual step is the point — it is the only
 * honest way to confirm money nobody's software saw arrive.
 */
export class BankTransferProvider implements PaymentProvider {
  readonly name = "bank_transfer";
  /** True: no simulation is involved, the instructions are real. */
  readonly liveMode = true;

  async createCheckout(request: CheckoutRequest): Promise<CheckoutSession> {
    return {
      checkoutUrl: `/donate/transfer/${encodeURIComponent(request.reference)}`,
      providerRef: null,
    };
  }

  async parseWebhook(): Promise<SettlementEvent | null> {
    return null; // Nothing calls back; staff reconcile it.
  }

  async cancelSubscription(): Promise<void> {
    // Standing orders are set up at the donor's own bank, not here.
  }
}

export interface BankDetails {
  accountName: string;
  bank: string;
  accountNumber: string;
  branch: string | null;
  swift: string | null;
  /** Paybill or till a Kenyan donor can pay into directly from M-Pesa. */
  paybill: string | null;
  paybillAccount: string | null;
}

/**
 * Where to send a transfer, from the environment. Returns null when nothing is
 * configured — the rail is then never offered, because publishing an incomplete
 * set of bank details is worse than not offering the option at all.
 */
export function bankDetails(): BankDetails | null {
  const accountName = process.env.BANK_ACCOUNT_NAME;
  const bank = process.env.BANK_NAME;
  const accountNumber = process.env.BANK_ACCOUNT_NUMBER;
  if (!accountName || !bank || !accountNumber) return null;

  return {
    accountName,
    bank,
    accountNumber,
    branch: process.env.BANK_BRANCH ?? null,
    swift: process.env.BANK_SWIFT ?? null,
    paybill: process.env.MPESA_PAYBILL_PUBLIC ?? process.env.MPESA_SHORTCODE ?? null,
    paybillAccount: process.env.MPESA_PAYBILL_ACCOUNT ?? null,
  };
}
