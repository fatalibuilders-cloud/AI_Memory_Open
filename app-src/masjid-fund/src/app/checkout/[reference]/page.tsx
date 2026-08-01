import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { INTENT_LABELS } from "@/lib/donation";
import { getDonationByReference } from "@/lib/donations";
import { formatMoney } from "@/lib/money";
import { getPaymentProvider } from "@/lib/payments";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Simulated checkout",
  robots: { index: false },
};

/**
 * Stand-in for a hosted payment page, used only when no real provider is
 * configured. It lets the whole donation journey be walked end to end —
 * including the failure path — without keys or a card.
 */
export default async function MockCheckoutPage({
  params,
  searchParams,
}: {
  params: Promise<{ reference: string }>;
  searchParams: Promise<{ failed?: string }>;
}) {
  if (getPaymentProvider().liveMode) notFound();

  const { reference } = await params;
  const { failed } = await searchParams;
  const donation = await getDonationByReference(reference);
  if (!donation) notFound();

  if (donation.status === "completed") {
    return (
      <div className="mx-auto max-w-lg px-4 py-24 text-center">
        <h1 className="font-display text-2xl font-semibold">This donation is already paid</h1>
        <Link
          href={`/donate/thank-you?ref=${donation.reference}`}
          className="mt-6 inline-block rounded-xl bg-masjid-700 px-6 py-3.5 font-semibold text-white hover:bg-masjid-800"
        >
          View your receipt
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-lg px-4 py-20">
      <div className="rounded-3xl border border-sand-200 bg-white p-8 shadow-sm">
        <p className="rounded-lg bg-brass-400/15 px-3 py-2 text-sm font-semibold text-sand-800">
          Test mode — this is a simulated payment page. No card is taken and no money moves.
        </p>

        <h1 className="mt-6 font-display text-2xl font-semibold">Confirm your donation</h1>
        <dl className="mt-6 divide-y divide-sand-200 rounded-2xl border border-sand-200">
          <Row label="Reference" value={donation.reference} />
          <Row
            label="Amount"
            value={`${formatMoney(donation.amountCents, donation.currency)}${
              donation.frequency === "monthly" ? " each month" : ""
            }`}
          />
          <Row label="Type" value={INTENT_LABELS[donation.intent]} />
          <Row label="Goes to" value={donation.projectName ?? "Where it is needed most"} />
        </dl>

        {failed && (
          <p role="alert" className="mt-6 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
            The simulated payment was declined. Nothing was charged.
          </p>
        )}

        <form action="/api/payments/mock-complete" method="post" className="mt-6 space-y-3">
          <input type="hidden" name="reference" value={donation.reference} />
          <button
            type="submit"
            name="outcome"
            value="completed"
            className="w-full rounded-xl bg-masjid-700 px-6 py-4 font-semibold text-white hover:bg-masjid-800"
          >
            Pay {formatMoney(donation.amountCents, donation.currency)} (simulated)
          </button>
          <button
            type="submit"
            name="outcome"
            value="failed"
            className="w-full rounded-xl border border-sand-300 px-6 py-3 font-semibold text-sand-800 hover:bg-sand-100"
          >
            Simulate a declined payment
          </button>
        </form>
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-2 px-5 py-3">
      <dt className="text-sm text-sand-700">{label}</dt>
      <dd className="font-semibold">{value}</dd>
    </div>
  );
}
