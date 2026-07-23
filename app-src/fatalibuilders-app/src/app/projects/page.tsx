import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";
import { getUserBySession } from "@/lib/auth";
import { readSessionCookie } from "@/lib/session-cookie";
import { listProjects } from "@/lib/projects";
import { NewProjectButton } from "@/components/NewProjectButton";

export const metadata: Metadata = { title: "Your projects — Fatalibuilders" };
export const dynamic = "force-dynamic";

export default async function ProjectsPage() {
  const user = await getUserBySession(await readSessionCookie());
  if (!user) redirect("/login");
  const projects = await listProjects(user.id);

  return (
    <main className="mx-auto flex max-w-2xl flex-col gap-6 px-6 py-12">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Your projects</h1>
        <NewProjectButton />
      </div>
      {projects.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-stone-300 p-10 text-center text-stone-500">
          <p className="font-medium">No projects yet.</p>
          <p className="mt-1 text-sm">
            Press <span className="font-semibold">+ New project</span> and enter your building&apos;s
            details — it takes about 10 minutes.
          </p>
        </div>
      ) : (
        <ul className="flex flex-col gap-3">
          {projects.map((p) => (
            <li key={p.id}>
              <Link
                href={p.status === "complete" ? `/projects/${p.id}` : `/projects/${p.id}/edit`}
                className="flex items-center justify-between rounded-xl border border-stone-200 bg-white px-4 py-3 hover:border-amber-400"
              >
                <span className="font-medium">{p.name}</span>
                <span
                  className={
                    p.status === "complete"
                      ? "rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800"
                      : "rounded-full bg-stone-100 px-2.5 py-0.5 text-xs font-medium text-stone-600"
                  }
                >
                  {p.status === "complete" ? "Complete" : "Draft"}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
