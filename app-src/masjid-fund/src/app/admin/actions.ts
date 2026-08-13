"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { AdminError, adminLogin, adminLogout, requireAdmin } from "@/lib/admin";
import {
  addProjectCost,
  costSchema,
  createProject,
  deleteProjectCost,
  parseOrThrow,
  postProjectUpdate,
  projectSchema,
  updateProject,
  updateSchema,
} from "@/lib/admin-data";
import { INTENTS, type Intent } from "@/lib/donation";
import { recordOfflineDonation } from "@/lib/donations";
import { parseAmountToCents } from "@/lib/money";

/**
 * Server actions behind the admin forms. Each one runs the work, then
 * redirects — carrying any message back in the query string, so the screens
 * stay server-rendered with no client-side form state.
 */

/** Runs `work`, returning the destination to redirect to. */
async function run(work: () => Promise<string>, onError: (message: string) => string) {
  let destination: string;
  try {
    destination = await work();
  } catch (err) {
    if (err instanceof AdminError) return onError(err.message);
    console.error("admin action failed:", err);
    return onError("Something went wrong. Try again.");
  }
  return destination;
}

export async function loginAction(formData: FormData) {
  const destination = await run(
    async () => {
      await adminLogin(String(formData.get("email") ?? ""), String(formData.get("password") ?? ""));
      return "/admin";
    },
    (message) => `/admin/login?error=${encodeURIComponent(message)}`,
  );
  redirect(destination);
}

export async function logoutAction() {
  await adminLogout();
  redirect("/admin/login");
}

export async function createProjectAction(formData: FormData) {
  const destination = await run(
    async () => {
      await requireAdmin();
      const input = parseOrThrow(projectSchema, readProject(formData));
      await createProject(input);
      revalidatePath("/projects");
      return `/admin/projects/${input.slug}?saved=1`;
    },
    (message) => `/admin/projects/new?error=${encodeURIComponent(message)}`,
  );
  redirect(destination);
}

export async function updateProjectAction(originalSlug: string, formData: FormData) {
  const destination = await run(
    async () => {
      await requireAdmin();
      const input = parseOrThrow(projectSchema, readProject(formData));
      await updateProject(originalSlug, input);
      revalidatePath("/projects");
      revalidatePath(`/projects/${input.slug}`);
      return `/admin/projects/${input.slug}?saved=1`;
    },
    (message) => `/admin/projects/${originalSlug}?error=${encodeURIComponent(message)}`,
  );
  redirect(destination);
}

export async function addCostAction(slug: string, formData: FormData) {
  const destination = await run(
    async () => {
      await requireAdmin();
      await addProjectCost(
        slug,
        parseOrThrow(costSchema, {
          label: String(formData.get("label") ?? ""),
          detail: String(formData.get("detail") ?? ""),
          unitCostCents: parseAmountToCents(String(formData.get("unitCost") ?? "")) ?? 0,
          position: Number(formData.get("position") ?? 0),
        }),
      );
      revalidatePath(`/projects/${slug}`);
      return `/admin/projects/${slug}?saved=1`;
    },
    (message) => `/admin/projects/${slug}?error=${encodeURIComponent(message)}`,
  );
  redirect(destination);
}

export async function deleteCostAction(slug: string, formData: FormData) {
  const destination = await run(
    async () => {
      await requireAdmin();
      await deleteProjectCost(String(formData.get("id") ?? ""));
      revalidatePath(`/projects/${slug}`);
      return `/admin/projects/${slug}?saved=1`;
    },
    (message) => `/admin/projects/${slug}?error=${encodeURIComponent(message)}`,
  );
  redirect(destination);
}

export async function postUpdateAction(slug: string, formData: FormData) {
  const destination = await run(
    async () => {
      await requireAdmin();
      await postProjectUpdate(
        slug,
        parseOrThrow(updateSchema, {
          title: String(formData.get("title") ?? ""),
          body: String(formData.get("body") ?? ""),
        }),
      );
      revalidatePath(`/projects/${slug}`);
      return `/admin/projects/${slug}?posted=1`;
    },
    (message) => `/admin/projects/${slug}?error=${encodeURIComponent(message)}`,
  );
  redirect(destination);
}

export async function recordOfflineAction(formData: FormData) {
  const destination = await run(
    async () => {
      await requireAdmin();
      const amountCents = parseAmountToCents(String(formData.get("amount") ?? ""));
      if (!amountCents) throw new AdminError("Enter the amount received, e.g. 500", 400);

      const intentRaw = String(formData.get("intent") ?? "sadaqah_jariyah");
      const intent = (INTENTS as readonly string[]).includes(intentRaw)
        ? (intentRaw as Intent)
        : "sadaqah_jariyah";
      const projectSlug = String(formData.get("projectSlug") ?? "");
      const email = String(formData.get("donorEmail") ?? "").trim();

      await recordOfflineDonation({
        amountCents,
        projectSlug: projectSlug || null,
        donorName: String(formData.get("donorName") ?? "").trim() || null,
        donorEmail: email || null,
        intent,
        note: String(formData.get("note") ?? "").trim() || null,
        anonymous: formData.get("anonymous") === "on",
      });
      revalidatePath("/projects");
      return "/admin/donations?recorded=1";
    },
    (message) => `/admin/donations?error=${encodeURIComponent(message)}`,
  );
  redirect(destination);
}

function readProject(formData: FormData) {
  return {
    slug: String(formData.get("slug") ?? ""),
    name: String(formData.get("name") ?? ""),
    city: String(formData.get("city") ?? ""),
    country: String(formData.get("country") ?? ""),
    summary: String(formData.get("summary") ?? ""),
    story: String(formData.get("story") ?? ""),
    status: String(formData.get("status") ?? "planning"),
    goalCents: parseAmountToCents(String(formData.get("goal") ?? "")) ?? 0,
    offlineRaisedCents: parseAmountToCents(String(formData.get("offlineRaised") ?? "0")) ?? 0,
    capacity: Number(formData.get("capacity") ?? 0),
    accent: String(formData.get("accent") ?? "emerald"),
    position: Number(formData.get("position") ?? 0),
  };
}
