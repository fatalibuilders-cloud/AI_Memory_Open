import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";
import { AuthError, getUserBySession } from "@/lib/auth";
import { readSessionCookie } from "@/lib/session-cookie";
import { getProject } from "@/lib/projects";
import { projectDataSchema, ROOF_TYPES, SOIL_TYPES, WALL_TYPES } from "@/lib/project-schema";
import { computeMaterials } from "@/engines/materials/residential";
import { computeCost } from "@/engines/cost";
import { ResultsView } from "@/components/ResultsView";
import { CostView } from "@/components/CostView";

export const metadata: Metadata = { title: "Project — Fatalibuilders" };
export const dynamic = "force-dynamic";

export default async function ProjectPage({ params }: { params: Promise<{ id: string }> }) {
  const user = await getUserBySession(await readSessionCookie());
  if (!user) redirect("/login");
  const { id } = await params;

  let project;
  try {
    project = await getProject(user.id, id);
  } catch (err) {
    if (err instanceof AuthError && err.status === 404) redirect("/projects");
    throw err;
  }
  if (project.status !== "complete") redirect(`/projects/${project.id}/edit`);
  const d = project.data;

  return (
    <main className="mx-auto flex max-w-xl flex-col gap-6 px-6 py-10">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">{project.name}</h1>
        <Link
          href={`/projects/${project.id}/edit`}
          className="text-sm font-medium text-amber-700 hover:underline"
        >
          Edit details
        </Link>
      </div>

      <div className="rounded-xl border border-stone-200 bg-white p-4 text-sm leading-6">
        <p>
          {d.country} · {d.floors} floor(s) · {d.footprintLengthM} × {d.footprintWidthM} m ·
          height {d.floorHeightM} m
        </p>
        <p>
          {WALL_TYPES[d.wallType ?? "concrete_block"]}, {d.wallThicknessMm} mm ·{" "}
          {ROOF_TYPES[d.roofType ?? "gable_iron_sheets"]}
        </p>
        <p>
          {d.doorsCount} doors · {d.windowsCount} windows · Soil:{" "}
          {SOIL_TYPES[d.soilType ?? "unknown"]}
        </p>
      </div>

      {(() => {
        const parsed = projectDataSchema.safeParse(d);
        if (!parsed.success) {
          return (
            <div className="rounded-xl border border-dashed border-amber-300 bg-amber-50 p-6 text-center text-sm text-amber-800">
              Some project details are missing — edit the project to complete them.
            </div>
          );
        }
        return (
          <>
            <ResultsView
              result={computeMaterials(parsed.data)}
              codeProfile={parsed.data.codeProfile}
            />
            <CostView result={computeCost(parsed.data)} />
          </>
        );
      })()}

      <div className="rounded-xl border border-dashed border-stone-300 bg-stone-50 p-4 text-center text-sm text-stone-600">
        Labor & time plan arrives next — it will use this same data automatically.
      </div>
    </main>
  );
}
