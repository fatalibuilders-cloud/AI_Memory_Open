import type { Metadata } from "next";
import Link from "next/link";
import { LegalPage } from "@/components/LegalPage";

// Organisation details come from the environment at request time. Without this
// the page is prerendered at build time and freezes whatever ORG_* held then —
// a deployment that sets them at runtime would publish a policy page claiming
// no registration exists.
export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Privacy",
  description:
    "What Masjid Fund collects from donors and applicants, why, how long it is kept, and who else sees it.",
};

export default function PrivacyPage() {
  return (
    <LegalPage
      title="Privacy"
      intro="What we collect, why we collect it, and what we will not do with it."
      updated="16 August 2026"
    >
      <section>
        <h2>If you donate</h2>
        <p>We record your name, email address, the amount, which project you chose, and any
          dedication or message you wrote. The email address is needed to send your receipt; the
          rest is the donation record itself.</p>
        <p>
          <strong>Card details never reach us.</strong> Payment happens on the payment
          provider&apos;s own page. We store their reference for the transaction so it can be
          reconciled and refunded, nothing more.
        </p>
        <p>If you tick &ldquo;give anonymously&rdquo;, your name is not shown anywhere public.
          It stays in our records, because the accounts have to add up and a refund has to be
          traceable.</p>
        <p>
          <strong>Giving by M-Pesa</strong> means we also hold the phone number you paid from. It
          is needed to send the payment prompt and to match the gift against the M-Pesa statement.
          It is never published and never used to market to you.
        </p>
      </section>

      <section>
        <h2>If you apply for funding</h2>
        <p>We collect what the form asks for: the masjid, the land and its title, the costs, the
          committee contact, and the documents you attach — typically a certified title deed,
          drawings and a bill of quantities.</p>
        <p>Those documents are visible only to staff reviewing the application. They are never
          published, never shown on a project page, and never sent to donors. If your application
          is approved, what becomes public is the project: the masjid, its location, its budget and
          its progress — not your paperwork or your phone number.</p>
      </section>

      <section>
        <h2>Technical records</h2>
        <p>When a donation or an application is submitted we store a one-way hash of the
          submitting IP address. It is used only to stop bursts of automated abuse — stolen cards
          being tested against the donation form, for instance. The hash is salted, so the address
          cannot be recovered from it, and we do not use it to build any profile of you.</p>
        <p>We do not use advertising trackers or third-party analytics. The only cookie the site
          sets is the session cookie for staff signing in to the admin screens.</p>
      </section>

      <section>
        <h2>Who else sees your data</h2>
        <ul>
          <li><strong>The payment provider</strong> — processes the payment and holds the card
            details we never see.</li>
          <li><strong>The email provider</strong> — delivers your receipt, so it handles your
            address and the contents of that email.</li>
          <li><strong>The hosting and database provider</strong> — stores the records described
            above on our behalf.</li>
        </ul>
        <p>We do not sell your data, and we do not share donor lists with other organisations,
          including the communities whose masajid you fund.</p>
      </section>

      <section>
        <h2>How long we keep it</h2>
        <p>Donation records are kept for seven years, which is what accounting and audit
          obligations require of a body handling public donations. Application documents are kept
          for the life of the project they support, and for two years after an application is
          declined, in case it is resubmitted.</p>
      </section>

      <section>
        <h2>Your rights</h2>
        <p>Under the Kenyan Data Protection Act 2019 — and comparable law wherever you are — you
          can ask us for a copy of what we hold about you, ask us to correct it, or ask us to
          delete it. Write to the address at the foot of this page and a person will answer.</p>
        <p>Deletion has one limit worth stating plainly: we cannot erase a donation from the
          financial records while we are legally obliged to keep them. We can remove your name
          from anything public and stop contacting you at once.</p>
      </section>

      <section>
        <h2>Changes</h2>
        <p>If this policy changes materially we will say so on this page and date it. The version
          you agreed to when you gave is the one that governs that donation.</p>
        <p>
          See also our <Link href="/terms" className="text-masjid-700 underline">terms</Link> and{" "}
          <Link href="/refunds" className="text-masjid-700 underline">refund policy</Link>.
        </p>
      </section>
    </LegalPage>
  );
}
