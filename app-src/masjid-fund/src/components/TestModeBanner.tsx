import { getPaymentProvider } from "@/lib/payments";

/**
 * Site-wide notice whenever payments are simulated. A preview deployment is
 * likely to be shared with a committee or a few donors for feedback, and
 * nobody should be able to reach the donate form believing their money moved.
 * Disappears by itself as soon as a real provider is configured.
 */
export function TestModeBanner() {
  if (getPaymentProvider().liveMode) return null;

  return (
    <div className="bg-brass-500 text-masjid-900">
      <p className="mx-auto max-w-6xl px-4 py-2 text-center text-sm font-medium">
        Test site — payments are simulated, no money is taken and no receipts are
        emailed.
      </p>
    </div>
  );
}
