import Link from "next/link";
import { redirect } from "next/navigation";
import { ProjectFields } from "@/components/admin/ProjectFields";
import { getAdminSession } from "@/lib/admin";
import { createProjectAction } from "../../actions";

export const dynamic = "force-dynamic";

export default async function NewProjectPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  if (!(await getAdminSession())) redirect("/admin/login");
  const { error } = await searchParams;

  return (
    <div className="max-w-3xl">
      <Link href="/admin/projects" className="text-sm text-sand-700 hover:text-masjid-900">
        ← Projects
      </Link>
      <h1 className="mt-3 font-display text-3xl font-semibold">Add a project</h1>
      <p className="mt-2 text-sand-700">
        Costed items and build updates are added once the project is saved.
      </p>

      <form action={createProjectAction} className="mt-8 space-y-6">
        <ProjectFields />
        {error && (
          <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </p>
        )}
        <button
          type="submit"
          className="rounded-xl bg-masjid-700 px-6 py-3.5 font-semibold text-white hover:bg-masjid-800"
        >
          Save project
        </button>
      </form>
    </div>
  );
}
