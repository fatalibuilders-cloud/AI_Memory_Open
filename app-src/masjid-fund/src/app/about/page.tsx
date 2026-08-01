import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "How it works",
  description:
    "How masjid projects are chosen, costed and built — and how donations are held, released and accounted for.",
};

const SECTIONS = [
  {
    title: "How a project gets listed",
    body: [
      "A community applies with the land title, a letter from the local council or waqf board, and an estimate of the congregation it serves.",
      "We visit the site, check that the land is titled to a trust rather than an individual, and have a quantity surveyor price a bill of quantities for the design.",
      "Only then does the project appear here, with its full budget and unit costs published on its page.",
    ],
  },
  {
    title: "How donations are held",
    body: [
      "Gifts to a named project go into an account restricted to that project. They cannot be moved to another build or spent on overheads.",
      "Money is released in stages against work certified on site — foundations, superstructure, roof, finishes — never as a lump sum up front.",
      "Gifts given 'where it is needed most' are allocated to whichever active project is closest to unblocking its next construction stage.",
    ],
  },
  {
    title: "Zakat is handled separately",
    body: [
      "Most scholars hold that masjid construction does not fall within the eight categories of zakat named in Surah at-Tawbah (9:60).",
      "Zakat given through this site is therefore never spent on building. It is recorded in a separate pool and passed to eligible recipients — in practice the poor and needy in the same communities.",
      "If you intend zakat, choose Zakat on the donation form and it will be routed accordingly.",
    ],
  },
  {
    title: "What happens at handover",
    body: [
      "The finished masjid is titled to a local waqf trust, which makes it a permanent endowment: it stays a place of prayer and cannot be sold or repurposed.",
      "Final accounts — budget against actual spend — are published on the project page.",
      "Maintenance and imam costs are the local community's responsibility, so donations here stay on construction.",
    ],
  },
];

export default function AboutPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-16">
      <h1 className="font-display text-4xl font-semibold sm:text-5xl">How it works</h1>
      <p className="mt-4 text-lg leading-relaxed text-sand-700">
        Masjid Fund exists to do one thing well: turn donations into finished masajid, with
        the numbers visible at every step.
      </p>

      <div className="mt-12 space-y-12">
        {SECTIONS.map((section) => (
          <section key={section.title}>
            <h2 className="font-display text-2xl font-semibold">{section.title}</h2>
            <div className="mt-3 space-y-3 leading-relaxed text-masjid-900/85">
              {section.body.map((paragraph) => (
                <p key={paragraph}>{paragraph}</p>
              ))}
            </div>
          </section>
        ))}
      </div>

      <div className="mt-14 rounded-2xl bg-masjid-800 p-8 text-sand-50">
        <h2 className="font-display text-2xl font-semibold">Ready to give?</h2>
        <p className="mt-2 text-sand-100/85">
          Choose a masjid, or let us apply your gift where the next stage is waiting on funds.
        </p>
        <Link
          href="/donate"
          className="mt-6 inline-block rounded-xl bg-brass-400 px-6 py-3.5 font-semibold text-masjid-900 hover:bg-brass-500"
        >
          Donate now
        </Link>
      </div>
    </div>
  );
}
