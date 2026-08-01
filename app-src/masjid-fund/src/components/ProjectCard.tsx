import Link from "next/link";
import { MasjidScene } from "./MasjidScene";
import { ProgressBar } from "./ProgressBar";
import { StatusBadge } from "./StatusBadge";
import type { Project } from "@/lib/projects";

export function ProjectCard({ project }: { project: Project }) {
  const done = project.status === "completed";
  return (
    <article className="group flex flex-col overflow-hidden rounded-2xl border border-sand-200 bg-white shadow-sm transition hover:shadow-md">
      <Link href={`/projects/${project.slug}`} className="block">
        <MasjidScene accent={project.accent} className="arch h-44 w-full" />
      </Link>

      <div className="flex flex-1 flex-col gap-3 p-5">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h3 className="font-display text-xl font-semibold leading-tight">
              <Link href={`/projects/${project.slug}`} className="hover:text-masjid-700">
                {project.name}
              </Link>
            </h3>
            <p className="mt-1 text-sm text-sand-700">
              {project.city}, {project.country} · {project.capacity} worshippers
            </p>
          </div>
          <StatusBadge status={project.status} />
        </div>

        <p className="text-sm leading-relaxed text-masjid-900/80">{project.summary}</p>

        <div className="mt-auto space-y-4 pt-2">
          <ProgressBar raisedCents={project.raisedCents} goalCents={project.goalCents} compact />
          <div className="flex items-center justify-between gap-3">
            <p className="text-xs text-sand-700">
              {project.donorCount === 0
                ? "Be the first to give"
                : `${project.donorCount.toLocaleString()} ${
                    project.donorCount === 1 ? "donor" : "donors"
                  }`}
            </p>
            {done ? (
              <Link
                href={`/projects/${project.slug}`}
                className="rounded-lg border border-masjid-700 px-3.5 py-1.5 text-sm font-semibold text-masjid-700 hover:bg-masjid-50"
              >
                See the result
              </Link>
            ) : (
              <Link
                href={`/donate?project=${project.slug}`}
                className="rounded-lg bg-masjid-700 px-3.5 py-1.5 text-sm font-semibold text-white hover:bg-masjid-800"
              >
                Donate
              </Link>
            )}
          </div>
        </div>
      </div>
    </article>
  );
}
