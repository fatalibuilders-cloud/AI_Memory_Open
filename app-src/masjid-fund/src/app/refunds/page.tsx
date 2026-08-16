import type { Metadata } from "next";
import Link from "next/link";
import { LegalPage } from "@/components/LegalPage";
import { getOrg } from "@/lib/org";

// Organisation details come from the environment at request time. Without this
// the page is prerendered at build time and freezes whatever ORG_* held then —
// a deployment that sets them at runtime would publish a policy page claiming
// no registration exists.
export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Refunds",
  description:
    "When Masjid Fund can refund a donation, how to ask, and what happens once funds have been released to a build.",
};

export default function RefundsPage() {
  const org = getOrg();

  return (
    <LegalPage
      title="Refunds"
      intro="Mistakes happen — a wrong amount, a duplicated gift, a monthly donation someone forgot about. Here is what we can undo, and when."
      updated="16 August 2026"
    >
      <section>
        <h2>Within 14 days, before the money is spent</h2>
        <p>Write to us within 14 days of giving, quoting the reference on your receipt, and we
          will refund in full — provided the funds have not yet been released to the contractor.
          You do not need to give a reason.</p>
      </section>

      <section>
        <h2>After funds are released</h2>
        <p>Once money has been paid out against certified work, it is in the building: blocks
          bought, a roof fixed, a wudu block plumbed. We cannot take that back, and it would be
          dishonest to pretend otherwise.</p>
        <p>Write to us anyway. If a gift was clearly a mistake — a duplicate, or a sum far larger
          than intended — we will look at what can be done, including applying it to a different
          project if that helps.</p>
      </section>

      <section>
        <h2>Duplicates and card errors</h2>
        <p>If the same donation was charged twice, tell us and we will refund the duplicate
          whatever the date. If you do not recognise a charge at all, contact us before disputing
          it with your bank — we can usually identify it the same day, and a chargeback costs the
          project more than the donation was worth.</p>
      </section>

      <section>
        <h2>Monthly giving</h2>
        <p>Cancelling stops future payments; it does not refund past ones. The link is in every
          receipt, and cancelling takes effect immediately. If a payment went out after you
          cancelled, that one is refunded in full.</p>
      </section>

      <section>
        <h2>How to ask</h2>
        <p>
          Email{" "}
          <a href={`mailto:${org.email}`} className="text-masjid-700 underline">
            {org.email}
          </a>{" "}
          with the reference from your receipt — it looks like <code>MF-7K2QX9T4</code> — and what
          you would like done. We aim to reply within three working days. Refunds return to the
          card or account they came from, and usually take five to ten days to appear.
        </p>
        <p>
          See also our <Link href="/terms" className="text-masjid-700 underline">terms</Link> and{" "}
          <Link href="/privacy" className="text-masjid-700 underline">privacy policy</Link>.
        </p>
      </section>
    </LegalPage>
  );
}
