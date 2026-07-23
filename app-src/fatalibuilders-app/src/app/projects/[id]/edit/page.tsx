import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { getUserBySession } from "@/lib/auth";
import { readSessionCookie } from "@/lib/session-cookie";
import { getProject } from "@/lib/projects";
import { ProjectWizard } from "@/components/ProjectWizard";
import { AuthError } from "@/lib/auth";

export const metadata: Metadata = { title: "Edit project — Fatalibuilders" };
export const dynamic = "force-dynamic";

export default async function EditProjectPage({ params }: { params: Promise<{ id: string }> }) {
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

  return (
    <main className="mx-auto flex max-w-xl flex-col gap-6 px-6 py-10">
      <h1 className="text-2xl font-bold">Enter your project</h1>
      <ProjectWizard project={project} />
    </main>
  );
}
