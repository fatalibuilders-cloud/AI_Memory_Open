import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Questions",
  description:
    "Common questions about donating to build a masjid — zakat, receipts, monthly giving, fees, refunds and how projects are verified.",
};

const FAQS = [
  {
    q: "Can I give my zakat towards building a masjid?",
    a: "Most scholars say no — masjid construction is not one of the eight categories in Surah at-Tawbah (9:60). If you select Zakat on the donation form, your gift is kept out of construction entirely and passed to eligible recipients instead. For building, choose Sadaqah Jariyah.",
  },
  {
    q: "What is Sadaqah Jariyah?",
    a: "An ongoing charity whose reward continues after the gift is made. A masjid is the classic example: for as long as people pray in it, the reward continues for those who built it.",
  },
  {
    q: "Do I get a receipt?",
    a: "Yes. Every completed donation gets an emailed receipt carrying a reference like MF-7K2QX9T4. Keep it — you can look up the status of any donation with it.",
  },
  {
    q: "How much of my donation reaches the build?",
    a: "Donations to a named project are restricted to that project's construction costs. Payment processing fees charged by the card networks are the only deduction, and they are shown in the project accounts.",
  },
  {
    q: "Can I fund something specific, like the roof?",
    a: "Yes. Each project page lists costed items — a truss, a square metre of walling, a wudu station — and the 'Fund this' button pre-fills that amount for you.",
  },
  {
    q: "Can I give monthly?",
    a: "Yes. Choose 'Give monthly' on the donation form. Monthly gifts are the most useful kind, because they let a build be scheduled with confidence. You can cancel any time from the link in your receipt.",
  },
  {
    q: "Can I donate in memory of someone?",
    a: "Yes — add a dedication on the form and it is recorded against the gift, for example on behalf of a parent who has passed away.",
  },
  {
    q: "What if a project raises more than its goal?",
    a: "Surplus stays within masjid construction. It goes first to the same project's remaining stages, and anything beyond that moves to the next project that is short of funds. The move is recorded in the published accounts.",
  },
  {
    q: "Can I get a refund?",
    a: "Contact us within 14 days and before the funds are released to the contractor, and we will refund in full. After work has been certified and paid for, the money is in the building.",
  },
  {
    q: "How do you verify a project is real?",
    a: "Land title checked, trust registration checked, a site visit before listing, and a quantity surveyor's priced bill of quantities. Build updates are published against each project as work progresses.",
  },
  {
    q: "Our community wants a masjid built. Can we apply?",
    a: "Yes — use the 'Apply for funding' page. You will need a certified title deed, architectural drawings, a priced bill of quantities, and one person on the committee we can reach. We verify each document and visit the site before listing anything, and we will come back to you for what is missing rather than simply refusing. Your documents and contact details are never published.",
  },
];

export default function FaqPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-16">
      <h1 className="font-display text-4xl font-semibold sm:text-5xl">Questions</h1>
      <p className="mt-4 text-lg text-sand-700">
        If yours is not answered here,{" "}
        <a href="mailto:salam@masjidfund.example" className="text-masjid-700 underline">
          email us
        </a>{" "}
        and a person will reply.
      </p>

      <dl className="mt-12 divide-y divide-sand-200 border-y border-sand-200">
        {FAQS.map((faq) => (
          <div key={faq.q} className="py-6">
            <dt className="font-display text-lg font-semibold">{faq.q}</dt>
            <dd className="mt-2 leading-relaxed text-masjid-900/85">{faq.a}</dd>
          </div>
        ))}
      </dl>

      <Link
        href="/donate"
        className="mt-12 inline-block rounded-xl bg-masjid-700 px-6 py-3.5 font-semibold text-white hover:bg-masjid-800"
      >
        Donate to a masjid
      </Link>
    </div>
  );
}
