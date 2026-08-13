import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import { ProjectFields } from "@/components/admin/ProjectFields";
import { getAdminSession } from "@/lib/admin";
import { formatMoney } from "@/lib/money";
import { getProjectBySlug } from "@/lib/projects";
import { addCostAction, deleteCostAction, postUpdateAction, updateProjectAction } from "../../actions";

export const dynamic = "force-dynamic";

export default async function EditProjectPage({
  params,
  searchParams,
}: {
  params: Promise<{ slug: string }>;
  searchParams: Promise<{ error?: string; saved?: string; posted?: string }>;
}) {
  if (!(await getAdminSession())) redirect("/admin/login");

  const { slug } = await params;
  const { error, saved, posted } = await searchParams;
  const project = await getProjectBySlug(slug);
  if (!project) notFound();

  // Server actions need the current slug bound; it can change on save.
  const saveProject = updateProjectAction.bind(null, slug);
  const addCost = addCostAction.bind(null, slug);
  const removeCost = deleteCostAction.bind(null, slug);
  const postUpdate = postUpdateAction.bind(null, slug);

  return (
    <div className="max-w-3xl">
      <Link href="/admin/projects" className="text-sm text-sand-700 hover:text-masjid-900">
        ← Projects
      </Link>
      <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
        <h1 className="font-display text-3xl font-semibold">{project.name}</h1>
        <Link
          href={`/projects/${project.slug}`}
          className="text-sm font-semibold text-masjid-700 hover:underline"
        >
          View public page →
        </Link>
      </div>
      <p className="mt-2 text-sand-700">
        {formatMoney(project.raisedCents)} raised of {formatMoney(project.goalCents)} ·{" "}
        {project.donorCount} donors
      </p>

      {(saved || posted) && (
        <p className="mt-6 rounded-xl bg-masjid-50 px-4 py-3 text-sm text-masjid-800">
          {posted ? "Update posted." : "Saved."}
        </p>
      )}
      {error && (
        <p role="alert" className="mt-6 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      )}

      <form action={saveProject} className="mt-8 space-y-6">
        <ProjectFields project={project} />
        <button
          type="submit"
          className="rounded-xl bg-masjid-700 px-6 py-3.5 font-semibold text-white hover:bg-masjid-800"
        >
          Save changes
        </button>
      </form>

      <section className="mt-14">
        <h2 className="font-display text-2xl font-semibold">Costed items</h2>
        <p className="mt-1 text-sand-700">
          These appear on the project page with a &ldquo;Fund this&rdquo; button.
        </p>

        <ul className="mt-4 divide-y divide-sand-200 overflow-hidden rounded-2xl border border-sand-200 bg-white">
          {project.costs.map((cost) => (
            <li key={cost.id} className="flex items-center justify-between gap-4 p-4">
              <div>
                <p className="font-semibold">{cost.label}</p>
                <p className="text-sm text-sand-700">{cost.detail}</p>
              </div>
              <div className="flex items-center gap-4">
                <span className="font-semibold">{formatMoney(cost.unitCostCents)}</span>
                <form action={removeCost}>
                  <input type="hidden" name="id" value={cost.id} />
                  <button type="submit" className="text-sm text-red-700 hover:underline">
                    Remove
                  </button>
                </form>
              </div>
            </li>
          ))}
          {project.costs.length === 0 && (
            <li className="p-4 text-sand-700">No costed items yet.</li>
          )}
        </ul>

        <form action={addCost} className="mt-4 grid gap-3 sm:grid-cols-4">
          <input
            name="label"
            placeholder="A roofing truss"
            required
            className="rounded-xl border border-sand-200 bg-white px-3 py-3 outline-none focus:ring-2 focus:ring-masjid-500 sm:col-span-1"
          />
          <input
            name="detail"
            placeholder="One of the 38 trusses spanning the hall."
            required
            className="rounded-xl border border-sand-200 bg-white px-3 py-3 outline-none focus:ring-2 focus:ring-masjid-500 sm:col-span-2"
          />
          <input
            name="unitCost"
            placeholder="220"
            required
            className="rounded-xl border border-sand-200 bg-white px-3 py-3 outline-none focus:ring-2 focus:ring-masjid-500"
          />
          <input type="hidden" name="position" value={project.costs.length + 1} />
          <button
            type="submit"
            className="rounded-xl border border-masjid-700 px-5 py-3 font-semibold text-masjid-700 hover:bg-masjid-50 sm:col-span-1"
          >
            Add item
          </button>
        </form>
      </section>

      <section className="mt-14">
        <h2 className="font-display text-2xl font-semibold">Post a build update</h2>
        <p className="mt-1 text-sand-700">
          Donors see these on the project page — this is how the build stays visible.
        </p>

        <form action={postUpdate} className="mt-4 space-y-3">
          <input
            name="title"
            placeholder="Roof complete"
            required
            className="w-full rounded-xl border border-sand-200 bg-white px-3 py-3 outline-none focus:ring-2 focus:ring-masjid-500"
          />
          <textarea
            name="body"
            rows={4}
            placeholder="What was done, what it cost, what comes next."
            required
            className="w-full rounded-xl border border-sand-200 bg-white px-3 py-3 outline-none focus:ring-2 focus:ring-masjid-500"
          />
          <button
            type="submit"
            className="rounded-xl bg-masjid-700 px-6 py-3.5 font-semibold text-white hover:bg-masjid-800"
          >
            Post update
          </button>
        </form>

        <ul className="mt-6 space-y-3">
          {project.updates.map((update) => (
            <li key={update.id} className="rounded-2xl border border-sand-200 bg-white p-4">
              <p className="text-xs text-sand-700">
                {new Date(update.postedAt).toLocaleString("en-GB")}
              </p>
              <p className="mt-1 font-semibold">{update.title}</p>
              <p className="mt-1 text-sm text-masjid-900/80">{update.body}</p>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
