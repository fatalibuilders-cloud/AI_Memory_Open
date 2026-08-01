import type { Metadata } from "next";
import Link from "next/link";
import { INTENT_LABELS } from "@/lib/donation";
import { getDonationByReference } from "@/lib/donations";
import { formatMoney } from "@/lib/money";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Thank you",
  description: "Your donation towards building a masjid.",
  robots: { index: false },
};

export default async function ThankYouPage({
  searchParams,
}: {
  searchParams: Promise<{ ref?: string }>;
}) {
  const { ref } = await searchParams;
  const donation = ref ? await getDonationByReference(ref) : null;

  if (!donation) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-24 text-center">
        <h1 className="font-display text-3xl font-semibold">We could not find that donation</h1>
        <p className="mt-3 text-sand-700">
          Check the reference in your receipt email, or contact us and we will look it up.
        </p>
        <Link
          href="/projects"
          className="mt-8 inline-block rounded-xl bg-masjid-700 px-6 py-3.5 font-semibold text-white hover:bg-masjid-800"
        >
          Back to the projects
        </Link>
      </div>
    );
  }

  const pending = donation.status === "pending";
  const failed = donation.status === "failed";

  return (
    <div className="mx-auto max-w-2xl px-4 py-20">
      <div className="rounded-3xl border border-sand-200 bg-white p-8 shadow-sm sm:p-10">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-brass-600">
          {failed ? "Payment not completed" : pending ? "Awaiting confirmation" : "Jazak Allahu khayran"}
        </p>
        <h1 className="mt-3 font-display text-3xl font-semibold sm:text-4xl">
          {failed
            ? "That payment did not go through"
            : pending
              ? "Your donation is being confirmed"
              : "Your donation is on its way to the build"}
        </h1>

        {!failed && !pending && (
          <p className="mt-4 leading-relaxed text-sand-700">
            May Allah accept it from you and make it a lasting sadaqah. A receipt is on its way
            to {maskEmail(donation.donorEmail)}.
          </p>
        )}
        {pending && (
          <p className="mt-4 leading-relaxed text-sand-700">
            We are waiting for the payment provider to confirm. This usually takes a few
            seconds — refresh this page, or check the receipt email we send once it settles.
          </p>
        )}
        {failed && (
          <p className="mt-4 leading-relaxed text-sand-700">
            Nothing has been charged. You are welcome to try again with another card.
          </p>
        )}

        <dl className="mt-8 divide-y divide-sand-200 rounded-2xl border border-sand-200">
          <Row label="Reference" value={donation.reference} />
          <Row
            label="Amount"
            value={`${formatMoney(donation.amountCents, donation.currency)}${
              donation.frequency === "monthly" ? " each month" : ""
            }`}
          />
          <Row label="Type" value={INTENT_LABELS[donation.intent]} />
          <Row
            label="Goes to"
            value={donation.projectName ?? "Where it is needed most"}
          />
          {donation.dedication && <Row label="Dedication" value={donation.dedication} />}
        </dl>

        <div className="mt-8 flex flex-wrap gap-3">
          {donation.projectSlug && (
            <Link
              href={`/projects/${donation.projectSlug}`}
              className="rounded-xl bg-masjid-700 px-6 py-3.5 font-semibold text-white hover:bg-masjid-800"
            >
              Follow the build
            </Link>
          )}
          <Link
            href="/projects"
            className="rounded-xl border border-masjid-700 px-6 py-3.5 font-semibold text-masjid-700 hover:bg-masjid-50"
          >
            See other projects
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

/** Confirms which address the receipt went to without printing it in full. */
function maskEmail(email: string): string {
  const [user, domain] = email.split("@");
  if (!domain) return "your inbox";
  const head = user.slice(0, 2);
  return `${head}${"•".repeat(Math.max(1, user.length - 2))}@${domain}`;
}
