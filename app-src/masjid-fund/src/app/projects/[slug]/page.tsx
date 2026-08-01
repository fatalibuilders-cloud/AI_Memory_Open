import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { MasjidScene } from "@/components/MasjidScene";
import { ProgressBar } from "@/components/ProgressBar";
import { StatusBadge } from "@/components/StatusBadge";
import { formatMoney } from "@/lib/money";
import { getProjectBySlug } from "@/lib/projects";

export const dynamic = "force-dynamic";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const project = await getProjectBySlug(slug);
  if (!project) return { title: "Project not found" };
  return {
    title: `${project.name}, ${project.city}`,
    description: project.summary,
  };
}

export default async function ProjectPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const project = await getProjectBySlug(slug);
  if (!project) notFound();

  const completed = project.status === "completed";
  const dateFormat = new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });

  return (
    <article>
      <header className="relative overflow-hidden bg-masjid-900 text-sand-50">
        {/* Artwork sits behind the title, dimmed so the text keeps its contrast. */}
        <div className="absolute inset-0" aria-hidden>
          <MasjidScene accent={project.accent} className="h-full w-full" />
          <div className="absolute inset-0 bg-masjid-900/70" />
        </div>
        <div className="relative mx-auto max-w-6xl px-4 py-20">
          <Link href="/projects" className="text-sm text-sand-100/80 hover:text-white">
            ← All projects
          </Link>
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <StatusBadge status={project.status} />
            <span className="text-sm text-sand-100/85">
              {project.city}, {project.country}
            </span>
          </div>
          <h1 className="mt-4 max-w-2xl font-display text-4xl font-semibold sm:text-5xl">
            {project.name}
          </h1>
          <p className="mt-4 max-w-2xl text-lg leading-relaxed text-sand-100/90">
            {project.summary}
          </p>
        </div>
      </header>

      <div className="mx-auto grid max-w-6xl gap-10 px-4 py-14 lg:grid-cols-[1.5fr_1fr]">
        <div className="space-y-12">
          <section>
            <h2 className="font-display text-2xl font-semibold">About this masjid</h2>
            <p className="mt-3 leading-relaxed text-masjid-900/85">{project.story}</p>

            <dl className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-4">
              <Fact label="Capacity" value={`${project.capacity} worshippers`} />
              <Fact label="Location" value={`${project.city}, ${project.country}`} />
              <Fact label="Total budget" value={formatMoney(project.goalCents)} />
              <Fact label="Donors so far" value={project.donorCount.toLocaleString()} />
            </dl>
          </section>

          {project.costs.length > 0 && (
            <section>
              <h2 className="font-display text-2xl font-semibold">What your donation buys</h2>
              <p className="mt-2 text-sand-700">
                Unit costs taken from the priced bill of quantities for this build.
              </p>
              <ul className="mt-6 divide-y divide-sand-200 overflow-hidden rounded-2xl border border-sand-200 bg-white">
                {project.costs.map((cost) => (
                  <li
                    key={cost.id}
                    className="flex flex-wrap items-center justify-between gap-4 p-5"
                  >
                    <div>
                      <p className="font-semibold">{cost.label}</p>
                      <p className="mt-0.5 text-sm text-sand-700">{cost.detail}</p>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className="font-display text-xl font-semibold text-masjid-700">
                        {formatMoney(cost.unitCostCents)}
                      </span>
                      {!completed && (
                        <Link
                          href={`/donate?project=${project.slug}&amount=${cost.unitCostCents}`}
                          className="rounded-lg border border-masjid-700 px-3 py-1.5 text-sm font-semibold text-masjid-700 hover:bg-masjid-50"
                        >
                          Fund this
                        </Link>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {project.updates.length > 0 && (
            <section>
              <h2 className="font-display text-2xl font-semibold">Build updates</h2>
              <ol className="mt-6 space-y-6 border-l-2 border-sand-200 pl-6">
                {project.updates.map((update) => (
                  <li key={update.id} className="relative">
                    <span
                      className="absolute -left-[31px] top-1.5 h-3 w-3 rounded-full bg-masjid-600"
                      aria-hidden
                    />
                    <p className="text-sm text-sand-700">
                      {dateFormat.format(new Date(update.postedAt))}
                    </p>
                    <h3 className="mt-1 font-display text-lg font-semibold">{update.title}</h3>
                    <p className="mt-1 leading-relaxed text-masjid-900/85">{update.body}</p>
                  </li>
                ))}
              </ol>
            </section>
          )}
        </div>

        {/* Donate panel */}
        <aside className="lg:sticky lg:top-24 lg:h-fit">
          <div className="rounded-2xl border border-sand-200 bg-white p-6 shadow-sm">
            <ProgressBar raisedCents={project.raisedCents} goalCents={project.goalCents} />

            {completed ? (
              <>
                <p className="mt-6 rounded-xl bg-masjid-50 p-4 text-sm leading-relaxed text-masjid-800">
                  This masjid is finished and in daily use. Donations now go to the masajid
                  still under construction.
                </p>
                <Link
                  href="/projects"
                  className="mt-4 block rounded-xl bg-masjid-700 px-6 py-3.5 text-center font-semibold text-white hover:bg-masjid-800"
                >
                  Fund another masjid
                </Link>
              </>
            ) : (
              <>
                <Link
                  href={`/donate?project=${project.slug}`}
                  className="mt-6 block rounded-xl bg-masjid-700 px-6 py-4 text-center text-base font-semibold text-white transition hover:bg-masjid-800"
                >
                  Donate to this masjid
                </Link>
                <Link
                  href={`/donate?project=${project.slug}&frequency=monthly`}
                  className="mt-3 block rounded-xl border border-masjid-700 px-6 py-3 text-center font-semibold text-masjid-700 hover:bg-masjid-50"
                >
                  Give monthly instead
                </Link>
                <p className="mt-4 text-xs leading-relaxed text-sand-700">
                  Funds for this project are held in a restricted account and released
                  against certified work on site.
                </p>
              </>
            )}
          </div>
        </aside>
      </div>
    </article>
  );
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-sand-200 bg-white p-4">
      <dt className="text-xs uppercase tracking-wide text-sand-700">{label}</dt>
      <dd className="mt-1 font-semibold">{value}</dd>
    </div>
  );
}
