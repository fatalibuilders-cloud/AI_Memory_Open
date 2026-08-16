import type { Metadata } from "next";
import Link from "next/link";
import { LegalPage } from "@/components/LegalPage";

// Organisation details come from the environment at request time. Without this
// the page is prerendered at build time and freezes whatever ORG_* held then —
// a deployment that sets them at runtime would publish a policy page claiming
// no registration exists.
export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Terms",
  description:
    "The terms on which Masjid Fund accepts donations, lists building projects, and reviews applications for funding.",
};

export default function TermsPage() {
  return (
    <LegalPage
      title="Terms"
      intro="The terms on which we accept donations, list projects and review applications."
      updated="16 August 2026"
    >
      <section>
        <h2>What a donation is</h2>
        <p>A donation is a gift towards the construction of a masjid. It is not an investment, a
          loan or a purchase: you receive no ownership, no return and no rights over the finished
          building, which belongs to the local trust that holds it.</p>
        <p>You confirm that the money is yours to give and that giving it does not break the law
          where you live.</p>
      </section>

      <section>
        <h2>Tax</h2>
        <p>A receipt from us acknowledges your gift. It is not a tax-deduction receipt, and
          donations are not deductible for US or UK tax purposes. If you need a deductible gift,
          give through a body registered for that purpose in your own country.</p>
      </section>

      <section>
        <h2>How your money is applied</h2>
        <p>Donations to a named project are restricted to that project&apos;s construction costs
          and released against work certified on site. Gifts given &ldquo;where it is needed
          most&rdquo; go to whichever active project is closest to unblocking its next stage.</p>
        <p>If a project raises more than its goal, the surplus stays within masjid construction:
          first to that project&apos;s remaining stages, then to the next project short of funds.
          If a project cannot proceed at all — a title dispute, a permit refused, a community that
          moves — the funds raised for it move to another masjid, and the reason is published on
          the project page.</p>
        <p>
          Zakat is never spent on construction. It is held separately and passed to eligible
          recipients, for the reasons set out in our{" "}
          <Link href="/faq" className="text-masjid-700 underline">questions page</Link>.
        </p>
      </section>

      <section>
        <h2>Monthly giving</h2>
        <p>A monthly gift continues until you stop it. Every receipt carries a link that cancels
          it, and cancelling takes effect before the next payment. Gifts already made are not
          refunded by cancelling — they are already in the building.</p>
      </section>

      <section>
        <h2>If you apply for funding</h2>
        <p>By applying you confirm that the information is true and the documents are genuine
          copies, and that you have the community&apos;s authority to make the application.</p>
        <p>We verify the title, the registration and the costs, and we visit the site. We may
          decline an application without giving a full reason, and we may stop or reverse funding
          if what we were told turns out to be untrue. Publishing a project is not a contract to
          fund it: what a project raises depends on donors.</p>
        <p>If your application is approved, you agree that we may publish the project details,
          costs and photographs of the build in order to raise funds for it. Your documents,
          contact details and phone number are not published.</p>
      </section>

      <section>
        <h2>Accuracy of what we publish</h2>
        <p>Budgets and progress figures come from the build accounts and the project committee,
          and are published as they reach us. Construction estimates change; where they do, the
          project page is updated rather than quietly corrected.</p>
      </section>

      <section>
        <h2>Liability</h2>
        <p>We are responsible for handling your donation as described here. We are not liable for
          delays caused by weather, permits, currency movements or the actions of a local
          contractor, beyond our obligation to release funds only against certified work and to
          report what happened.</p>
      </section>

      <section>
        <h2>Law</h2>
        <p>These terms are governed by the laws of Kenya, and the courts of Kenya have
          jurisdiction over any dispute arising from them.</p>
        <p>
          See also our <Link href="/privacy" className="text-masjid-700 underline">privacy policy</Link>{" "}
          and <Link href="/refunds" className="text-masjid-700 underline">refund policy</Link>.
        </p>
      </section>
    </LegalPage>
  );
}
