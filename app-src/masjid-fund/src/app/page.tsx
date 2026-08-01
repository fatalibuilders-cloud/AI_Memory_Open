import Link from "next/link";
import { MasjidScene } from "@/components/MasjidScene";
import { ProjectCard } from "@/components/ProjectCard";
import { formatMoney, formatMoneyCompact } from "@/lib/money";
import { getFundStats, listProjects, listRecentDonations } from "@/lib/projects";

export const dynamic = "force-dynamic";

const COSTS = [
  { amount: 2500, label: "Bags of cement", detail: "Roughly three square metres of floor." },
  { amount: 4500, label: "A square metre of wall", detail: "Blocks, mortar and plaster." },
  { amount: 22000, label: "A roof truss", detail: "One span of the prayer hall roof." },
  { amount: 60000, label: "A wudu station", detail: "Tap, drainage and seating." },
];

const STEPS = [
  {
    title: "Choose a masjid",
    body: "Every project is proposed by a local community, costed by a quantity surveyor and checked on site before it is listed.",
  },
  {
    title: "Give once or monthly",
    body: "Pick an amount or fund a specific item — a truss, a wall, a wudu station. You get a receipt with a reference the same minute.",
  },
  {
    title: "Follow it to completion",
    body: "Build updates and accounts are published against the project page until the keys are handed to the local waqf trust.",
  },
];

export default async function Home() {
  const [stats, projects, recent] = await Promise.all([
    getFundStats(),
    listProjects(),
    listRecentDonations(4),
  ]);
  const featured = projects.filter((p) => p.status !== "completed").slice(0, 3);

  return (
    <>
      {/* Hero */}
      <section className="relative overflow-hidden bg-masjid-900 text-sand-50">
        <div className="pattern-stars absolute inset-0 opacity-[0.12]" aria-hidden />
        <div className="relative mx-auto grid max-w-6xl gap-12 px-4 py-20 lg:grid-cols-[1.1fr_0.9fr] lg:items-center lg:py-28">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-brass-400">
              Sadaqah Jariyah
            </p>
            <h1 className="mt-4 font-display text-4xl font-semibold leading-[1.1] sm:text-5xl lg:text-6xl">
              Build a masjid that keeps giving long after you.
            </h1>
            <p className="mt-6 max-w-xl text-lg leading-relaxed text-sand-100/85">
              Communities bring the land and the labour. You cover the blocks, the roof and
              the water. Every project on this page is costed line by line, and you can see
              exactly what your donation buys.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link
                href="/donate"
                className="rounded-xl bg-brass-400 px-6 py-3.5 font-semibold text-masjid-900 shadow-sm transition hover:bg-brass-500"
              >
                Donate now
              </Link>
              <Link
                href="/projects"
                className="rounded-xl border border-sand-100/30 px-6 py-3.5 font-semibold text-sand-50 transition hover:bg-white/10"
              >
                See the projects
              </Link>
            </div>

            <blockquote className="mt-10 max-w-lg border-l-2 border-brass-400 pl-4 text-sand-100/85">
              <p className="font-display text-lg leading-relaxed">
                “Whoever builds a masjid for Allah, Allah will build for him a house like it
                in Paradise.”
              </p>
              <footer className="mt-2 text-sm text-sand-200/70">
                Sahih al-Bukhari 450 · Sahih Muslim 533
              </footer>
            </blockquote>
          </div>

          <MasjidScene className="hidden h-96 rounded-3xl lg:block" />
        </div>

        {/* Totals strip */}
        <div className="relative border-t border-white/10 bg-masjid-800/60">
          <dl className="mx-auto grid max-w-6xl grid-cols-2 gap-6 px-4 py-8 lg:grid-cols-4">
            <Stat value={formatMoneyCompact(stats.raisedCents)} label="Raised for construction" />
            <Stat value={stats.donorCount.toLocaleString()} label="Donations received" />
            <Stat value={String(stats.projectsActive)} label="Masajid being built" />
            <Stat
              value={stats.worshippersServed.toLocaleString()}
              label="Worshippers these masajid will hold"
            />
          </dl>
        </div>
      </section>

      {/* Featured projects */}
      <section className="mx-auto max-w-6xl px-4 py-20">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h2 className="font-display text-3xl font-semibold sm:text-4xl">
              Masajid waiting to be built
            </h2>
            <p className="mt-2 max-w-2xl text-sand-700">
              Each one has land, drawings and a local committee already in place.
            </p>
          </div>
          <Link href="/projects" className="font-semibold text-masjid-700 hover:text-masjid-900">
            View all projects →
          </Link>
        </div>

        <div className="mt-10 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {featured.map((project) => (
            <ProjectCard key={project.slug} project={project} />
          ))}
        </div>
      </section>

      {/* What a gift buys */}
      <section className="bg-sand-100 py-20">
        <div className="mx-auto max-w-6xl px-4">
          <h2 className="font-display text-3xl font-semibold sm:text-4xl">
            What your donation actually buys
          </h2>
          <p className="mt-2 max-w-2xl text-sand-700">
            Nothing here is a vague appeal. Costs come straight from the priced bill of
            quantities for each build.
          </p>
          <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {COSTS.map((cost) => (
              <div
                key={cost.label}
                className="rounded-2xl border border-sand-200 bg-white p-6 shadow-sm"
              >
                <p className="font-display text-3xl font-semibold text-masjid-700">
                  {formatMoney(cost.amount)}
                </p>
                <p className="mt-2 font-semibold">{cost.label}</p>
                <p className="mt-1 text-sm text-sand-700">{cost.detail}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="mx-auto max-w-6xl px-4 py-20">
        <h2 className="font-display text-3xl font-semibold sm:text-4xl">How it works</h2>
        <ol className="mt-10 grid gap-8 md:grid-cols-3">
          {STEPS.map((step, i) => (
            <li key={step.title} className="border-t-2 border-brass-400 pt-5">
              <p className="font-display text-sm font-semibold text-brass-600">
                Step {i + 1}
              </p>
              <h3 className="mt-1 font-display text-xl font-semibold">{step.title}</h3>
              <p className="mt-2 leading-relaxed text-sand-700">{step.body}</p>
            </li>
          ))}
        </ol>
      </section>

      {/* Trust */}
      <section className="bg-masjid-800 py-20 text-sand-50">
        <div className="mx-auto grid max-w-6xl gap-10 px-4 lg:grid-cols-2">
          <div>
            <h2 className="font-display text-3xl font-semibold sm:text-4xl">
              Where the money goes, in the open
            </h2>
            <p className="mt-4 leading-relaxed text-sand-100/85">
              Donations sit in a project-restricted account and are released against
              certified work on site. Every masjid is titled to a local waqf trust, so it
              stays a place of prayer permanently and can never be sold.
            </p>
            <Link
              href="/about"
              className="mt-6 inline-block rounded-xl border border-sand-100/30 px-5 py-3 font-semibold hover:bg-white/10"
            >
              Read our governance
            </Link>
          </div>
          <ul className="grid gap-4 sm:grid-cols-2">
            {[
              ["Costed builds", "Bill of quantities priced by an independent surveyor."],
              ["Staged release", "Funds released per certified construction stage."],
              ["Published accounts", "Final accounts posted on the project page."],
              ["Zakat kept separate", "Zakat is never spent on construction."],
            ].map(([title, body]) => (
              <li key={title} className="rounded-2xl bg-white/5 p-5">
                <p className="font-semibold text-brass-400">{title}</p>
                <p className="mt-1 text-sm text-sand-100/80">{body}</p>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* Recent donations */}
      {recent.length > 0 && (
        <section className="mx-auto max-w-6xl px-4 py-20">
          <h2 className="font-display text-3xl font-semibold">Recent gifts</h2>
          <ul className="mt-8 grid gap-4 sm:grid-cols-2">
            {recent.map((donation, i) => (
              <li
                key={`${donation.createdAt}-${i}`}
                className="rounded-2xl border border-sand-200 bg-white p-5"
              >
                <p className="font-semibold">
                  {donation.name} gave {formatMoney(donation.amountCents)}
                  {donation.projectName ? ` to ${donation.projectName}` : ""}
                </p>
                {donation.dedication && (
                  <p className="mt-1 text-sm italic text-sand-700">“{donation.dedication}”</p>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Closing CTA */}
      <section className="mx-auto max-w-4xl px-4 pb-24 text-center">
        <h2 className="font-display text-3xl font-semibold sm:text-4xl">
          A masjid is built one donation at a time.
        </h2>
        <p className="mx-auto mt-3 max-w-xl text-sand-700">
          Give once, or set aside a small amount each month and watch the walls go up.
        </p>
        <Link
          href="/donate"
          className="mt-8 inline-block rounded-xl bg-masjid-700 px-8 py-4 text-lg font-semibold text-white transition hover:bg-masjid-800"
        >
          Donate to a masjid
        </Link>
      </section>
    </>
  );
}

function Stat({ value, label }: { value: string; label: string }) {
  return (
    <div>
      <dt className="sr-only">{label}</dt>
      <dd>
        <span className="block font-display text-3xl font-semibold text-brass-400">
          {value}
        </span>
        <span className="mt-1 block text-sm text-sand-100/75">{label}</span>
      </dd>
    </div>
  );
}
