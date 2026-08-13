import type { Metadata } from "next";
import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import { INTENT_LABELS } from "@/lib/donation";
import { cancelMonthlyGiving, getDonationByManageToken } from "@/lib/donations";
import { formatMoney } from "@/lib/money";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Your monthly giving",
  robots: { index: false, follow: false },
};

/**
 * Donor self-service for a monthly gift. The link in the receipt is the
 * credential — no account, no password, and nothing here reveals anything a
 * donor could not already read in their own email.
 */
export default async function ManageGivingPage({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const { token } = await params;
  const donation = await getDonationByManageToken(token);
  if (!donation || donation.frequency !== "monthly") notFound();

  async function cancel() {
    "use server";
    await cancelMonthlyGiving(token);
    redirect(`/giving/${token}?cancelled=1`);
  }

  const cancelled = Boolean(donation.cancelledAt);

  return (
    <div className="mx-auto max-w-2xl px-4 py-20">
      <div className="rounded-3xl border border-sand-200 bg-white p-8 shadow-sm sm:p-10">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-brass-600">
          Monthly giving
        </p>
        <h1 className="mt-3 font-display text-3xl font-semibold">
          {formatMoney(donation.amountCents, donation.currency)} each month
          {donation.projectName ? ` to ${donation.projectName}` : ""}
        </h1>

        <dl className="mt-8 divide-y divide-sand-200 rounded-2xl border border-sand-200">
          <Row label="Reference" value={donation.reference} />
          <Row label="Type" value={INTENT_LABELS[donation.intent]} />
          <Row label="Goes to" value={donation.projectName ?? "Where it is needed most"} />
          <Row
            label="Status"
            value={
              cancelled
                ? "Cancelled — nothing further will be charged"
                : donation.status === "completed"
                  ? "Active"
                  : "Awaiting first payment"
            }
          />
        </dl>

        {cancelled ? (
          <p className="mt-8 rounded-xl bg-masjid-50 p-4 leading-relaxed text-masjid-800">
            This monthly gift has been cancelled. Everything you have already given stays with
            the project it was given to, and the build continues. Jazak Allahu khayran.
          </p>
        ) : (
          <>
            <p className="mt-8 leading-relaxed text-sand-700">
              You can stop this monthly gift at any time. Donations already made are not
              affected — they are in the building.
            </p>
            <form action={cancel} className="mt-6">
              <button
                type="submit"
                className="rounded-xl border border-red-300 px-6 py-3.5 font-semibold text-red-700 transition hover:bg-red-50"
              >
                Cancel monthly giving
              </button>
            </form>
          </>
        )}

        <div className="mt-10 border-t border-sand-200 pt-6">
          <Link href="/projects" className="font-semibold text-masjid-700 hover:text-masjid-900">
            See the projects you are supporting →
          </Link>
        </div>
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
