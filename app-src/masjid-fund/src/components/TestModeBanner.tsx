import { anyLiveMethod, bankDetails } from "@/lib/payments";

/**
 * Site-wide notice whenever the card, M-Pesa and PayPal rails are simulated. A
 * preview deployment is likely to be shared with a committee or a few donors
 * for feedback, and nobody should reach the donate form believing their money
 * moved. Disappears by itself once a real provider is configured.
 *
 * Bank transfer is called out separately: those details are real whenever they
 * are configured, and a donor who follows them really does send money — so the
 * banner must not tell them otherwise.
 */
export function TestModeBanner() {
  if (anyLiveMethod()) return null;
  const transfersAreReal = bankDetails() !== null;

  return (
    <div className="bg-brass-500 text-masjid-900">
      <p className="mx-auto max-w-6xl px-4 py-2 text-center text-sm font-medium">
        Test site — card, M-Pesa and PayPal payments are simulated, no money is taken and no
        receipts are emailed.
        {transfersAreReal && " Bank transfer details, however, are real."}
      </p>
    </div>
  );
}
