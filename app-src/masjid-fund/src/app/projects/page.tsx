import type { Metadata } from "next";
import { ProjectCard } from "@/components/ProjectCard";
import { listProjects } from "@/lib/projects";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Masjid building projects",
  description:
    "Browse masjid construction projects you can fund — location, capacity, budget and progress for each build.",
};

export default async function ProjectsPage() {
  const projects = await listProjects();
  const active = projects.filter((p) => p.status !== "completed");
  const completed = projects.filter((p) => p.status === "completed");

  return (
    <div className="mx-auto max-w-6xl px-4 py-16">
      <header className="max-w-2xl">
        <h1 className="font-display text-4xl font-semibold sm:text-5xl">Building projects</h1>
        <p className="mt-4 text-lg leading-relaxed text-sand-700">
          Every project below has donated land, approved drawings and a local committee
          responsible for the build. Choose one, or give where it is needed most.
        </p>
      </header>

      <section className="mt-12">
        <h2 className="font-display text-2xl font-semibold">Open for donations</h2>
        <div className="mt-6 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {active.map((project) => (
            <ProjectCard key={project.slug} project={project} />
          ))}
        </div>
        {active.length === 0 && (
          <p className="mt-6 rounded-2xl border border-sand-200 bg-white p-6 text-sand-700">
            Every listed masjid is fully funded. New projects are added each quarter.
          </p>
        )}
      </section>

      {completed.length > 0 && (
        <section className="mt-16">
          <h2 className="font-display text-2xl font-semibold">Completed</h2>
          <p className="mt-2 text-sand-700">
            Built, handed over and in daily use — with final accounts published.
          </p>
          <div className="mt-6 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {completed.map((project) => (
              <ProjectCard key={project.slug} project={project} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
