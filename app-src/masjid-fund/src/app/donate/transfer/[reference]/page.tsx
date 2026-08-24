import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { INTENT_LABELS } from "@/lib/donation";
import { getDonationByReference } from "@/lib/donations";
import { formatMoney, fromBase } from "@/lib/money";
import { bankDetails } from "@/lib/payments";
import { getOrg } from "@/lib/org";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "How to send your transfer",
  robots: { index: false, follow: false },
};

/**
 * Instructions for a gift the donor sends themselves. The reference is the
 * whole mechanism: it is what lets staff match the money to this record when
 * it lands, so it is repeated everywhere it might be needed.
 */
export default async function TransferPage({
  params,
}: {
  params: Promise<{ reference: string }>;
}) {
  const { reference } = await params;
  const donation = await getDonationByReference(reference);
  if (!donation || donation.method !== "bank") notFound();

  const details = bankDetails();
  if (!details) notFound();
  const org = getOrg();
  const settled = donation.status === "completed";

  return (
    <div className="mx-auto max-w-2xl px-4 py-16">
      <p className="text-sm font-semibold uppercase tracking-[0.2em] text-brass-600">
        {settled ? "Received" : "Almost there"}
      </p>
      <h1 className="mt-3 font-display text-3xl font-semibold sm:text-4xl">
        {settled ? "Your transfer has been matched" : "Send your transfer"}
      </h1>

      {settled ? (
        <p className="mt-4 leading-relaxed text-sand-700">
          We have matched your transfer against the account and it now counts towards the build.
          Jazak Allahu khayran.
        </p>
      ) : (
        <p className="mt-4 leading-relaxed text-sand-700">
          Nothing has been taken from you — a transfer is something you send. Use the details
          below, and quote the reference so we can match it when it lands. We check the account
          each working day and email you once it is matched.
        </p>
      )}

      <div className="mt-8 rounded-2xl border-2 border-masjid-700 bg-masjid-50 p-5 text-center">
        <p className="text-sm text-masjid-800">Quote this reference</p>
        <p className="mt-1 font-mono text-2xl font-bold tracking-wider text-masjid-900">
          {donation.reference}
        </p>
      </div>

      <dl className="mt-6 divide-y divide-sand-200 rounded-2xl border border-sand-200 bg-white">
        <Row label="Amount to send" value={formatMoney(donation.amountCents, donation.currency)} />
        <Row
          label="Or in shillings"
          value={`about ${formatMoney(fromBase(donation.baseAmountCents, "KES"), "KES")}`}
        />
        <Row label="Account name" value={details.accountName} />
        <Row label="Bank" value={details.bank} />
        <Row label="Account number" value={details.accountNumber} />
        {details.branch && <Row label="Branch" value={details.branch} />}
        {details.swift && <Row label="SWIFT / BIC" value={`${details.swift} (from abroad)`} />}
      </dl>

      {details.paybill && (
        <div className="mt-6 rounded-2xl border border-sand-200 bg-white p-5">
          <p className="font-semibold">Paying from M-Pesa instead</p>
          <p className="mt-2 text-sm leading-relaxed text-sand-700">
            Lipa na M-Pesa → Pay Bill → business number{" "}
            <strong className="text-masjid-900">{details.paybill}</strong>
            {details.paybillAccount ? (
              <>
                , account <strong className="text-masjid-900">{details.paybillAccount}</strong>
              </>
            ) : (
              <>
                , account <strong className="text-masjid-900">{donation.reference}</strong>
              </>
            )}
            .
          </p>
        </div>
      )}

      <dl className="mt-6 divide-y divide-sand-200 rounded-2xl border border-sand-200 bg-white">
        <Row label="Type" value={INTENT_LABELS[donation.intent]} />
        <Row label="Goes to" value={donation.projectName ?? "Where it is needed most"} />
      </dl>

      <p className="mt-6 text-sm leading-relaxed text-sand-700">
        If the reference is missed or the amount differs, email{" "}
        <a href={`mailto:${org.email}`} className="text-masjid-700 underline">
          {org.email}
        </a>{" "}
        with the date and amount and we will find it. Nothing counts towards the masjid until the
        money is in the account and matched.
      </p>

      <Link
        href={donation.projectSlug ? `/projects/${donation.projectSlug}` : "/projects"}
        className="mt-8 inline-block rounded-xl border border-masjid-700 px-6 py-3.5 font-semibold text-masjid-700 hover:bg-masjid-50"
      >
        {donation.projectSlug ? "Back to the project" : "See the projects"}
      </Link>
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
