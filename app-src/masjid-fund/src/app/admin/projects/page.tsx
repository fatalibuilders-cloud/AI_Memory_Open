import Link from "next/link";
import { redirect } from "next/navigation";
import { getAdminSession } from "@/lib/admin";
import { formatMoney, progressPercent } from "@/lib/money";
import { listProjects } from "@/lib/projects";

export const dynamic = "force-dynamic";

export default async function AdminProjectsPage() {
  if (!(await getAdminSession())) redirect("/admin/login");
  const projects = await listProjects();

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="font-display text-3xl font-semibold">Projects</h1>
        <Link
          href="/admin/projects/new"
          className="rounded-xl bg-masjid-700 px-5 py-3 font-semibold text-white hover:bg-masjid-800"
        >
          Add a project
        </Link>
      </div>

      <div className="mt-8 overflow-x-auto rounded-2xl border border-sand-200 bg-white">
        <table className="w-full text-sm">
          <thead className="border-b border-sand-200 text-left text-sand-700">
            <tr>
              <th className="p-3 font-medium">Project</th>
              <th className="p-3 font-medium">Status</th>
              <th className="p-3 font-medium">Raised</th>
              <th className="p-3 font-medium">Goal</th>
              <th className="p-3 font-medium">Donors</th>
              <th className="p-3" />
            </tr>
          </thead>
          <tbody className="divide-y divide-sand-200">
            {projects.map((project) => (
              <tr key={project.slug}>
                <td className="p-3">
                  <span className="font-semibold">{project.name}</span>
                  <span className="block text-xs text-sand-700">
                    {project.city}, {project.country}
                  </span>
                </td>
                <td className="p-3">{project.status}</td>
                <td className="p-3">
                  {formatMoney(project.raisedCents)}{" "}
                  <span className="text-sand-700">
                    ({progressPercent(project.raisedCents, project.goalCents)}%)
                  </span>
                </td>
                <td className="p-3">{formatMoney(project.goalCents)}</td>
                <td className="p-3">{project.donorCount}</td>
                <td className="p-3 text-right">
                  <Link
                    href={`/admin/projects/${project.slug}`}
                    className="font-semibold text-masjid-700 hover:underline"
                  >
                    Edit
                  </Link>
                </td>
              </tr>
            ))}
            {projects.length === 0 && (
              <tr>
                <td colSpan={6} className="p-6 text-center text-sand-700">
                  No projects yet — add the first one.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
