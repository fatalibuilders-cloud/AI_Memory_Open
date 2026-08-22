import type { Metadata } from "next";
import { notFound, redirect } from "next/navigation";
import { MpesaWaiting } from "@/components/MpesaWaiting";
import { INTENT_LABELS } from "@/lib/donation";
import { getDonationByReference } from "@/lib/donations";
import { formatMoney } from "@/lib/money";
import { getPaymentProvider } from "@/lib/payments";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Confirm on your phone",
  robots: { index: false, follow: false },
};

export default async function MpesaWaitingPage({
  params,
}: {
  params: Promise<{ reference: string }>;
}) {
  const { reference } = await params;
  const donation = await getDonationByReference(reference);
  if (!donation || donation.method !== "mpesa") notFound();
  if (donation.status === "completed") redirect(`/donate/thank-you?ref=${donation.reference}`);

  const simulated = !getPaymentProvider("mpesa").liveMode;

  return (
    <div className="mx-auto max-w-lg px-4 py-20">
      <MpesaWaiting
        reference={donation.reference}
        phoneHint={donation.phone ? donation.phone.slice(-3) : null}
        simulated={simulated}
      />

      <dl className="mt-8 divide-y divide-sand-200 rounded-2xl border border-sand-200 bg-white">
        <Row label="Reference" value={donation.reference} />
        <Row label="Amount" value={formatMoney(donation.amountCents, donation.currency)} />
        <Row label="Type" value={INTENT_LABELS[donation.intent]} />
        <Row label="Goes to" value={donation.projectName ?? "Where it is needed most"} />
      </dl>

      {simulated && (
        <form action="/api/payments/mock-complete" method="post" className="mt-6 space-y-3">
          <input type="hidden" name="reference" value={donation.reference} />
          <button
            type="submit"
            name="outcome"
            value="completed"
            className="w-full rounded-xl bg-masjid-700 px-6 py-4 font-semibold text-white hover:bg-masjid-800"
          >
            Simulate entering the PIN
          </button>
          <button
            type="submit"
            name="outcome"
            value="failed"
            className="w-full rounded-xl border border-sand-300 px-6 py-3 font-semibold text-sand-800 hover:bg-sand-100"
          >
            Simulate cancelling the prompt
          </button>
        </form>
      )}

      <p className="mt-6 text-center text-xs leading-relaxed text-sand-700">
        Donations over M-Pesa are charged in Kenyan shillings, converted from the amount you chose
        at the rate shown on the receipt.
      </p>
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
