import { z } from "zod";
import { getDb } from "@/db";
import { AdminError } from "./admin";
import { toCents } from "./money";

/**
 * Queries and mutations behind the admin screens. Every function here assumes
 * the caller has already passed requireAdmin().
 */

export const projectSchema = z.object({
  slug: z
    .string()
    .trim()
    .min(3, "Slug must be at least 3 characters")
    .max(120)
    .regex(/^[a-z0-9-]+$/, "Slug can use lowercase letters, numbers and hyphens only"),
  name: z.string().trim().min(2, "Name is required").max(120),
  city: z.string().trim().min(1, "City is required").max(80),
  country: z.string().trim().min(1, "Country is required").max(80),
  summary: z.string().trim().min(10, "Write a one-line summary").max(400),
  story: z.string().trim().min(20, "Tell donors about this masjid").max(4000),
  status: z.enum(["planning", "building", "completed"]),
  goalCents: z.number().int().min(100, "Set a budget"),
  offlineRaisedCents: z.number().int().min(0),
  capacity: z.number().int().min(0).max(100000),
  accent: z.enum(["emerald", "teal", "sky", "amber"]),
  position: z.number().int().min(0).max(999),
});

export type ProjectInput = z.infer<typeof projectSchema>;

export const costSchema = z.object({
  label: z.string().trim().min(2, "Name the item").max(120),
  detail: z.string().trim().min(2, "Explain what it covers").max(300),
  unitCostCents: z.number().int().min(1, "Set a unit cost"),
  position: z.number().int().min(0).max(999),
});

export const updateSchema = z.object({
  title: z.string().trim().min(3, "Give the update a title").max(160),
  body: z.string().trim().min(10, "Write the update").max(4000),
});

export function parseOrThrow<T>(schema: z.ZodType<T>, raw: unknown): T {
  const result = schema.safeParse(raw);
  if (!result.success) {
    throw new AdminError(result.error.issues[0]?.message ?? "Check the form and try again", 400);
  }
  return result.data;
}

export async function createProject(input: ProjectInput): Promise<void> {
  const db = await getDb();
  const clash = await db.query("SELECT 1 FROM projects WHERE slug = $1", [input.slug]);
  if (clash.length > 0) throw new AdminError("A project with that slug already exists.", 409);

  await db.query(
    `INSERT INTO projects
       (slug, name, city, country, summary, story, status, goal_cents,
        offline_raised_cents, capacity, accent, position)
     VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)`,
    [
      input.slug,
      input.name,
      input.city,
      input.country,
      input.summary,
      input.story,
      input.status,
      input.goalCents,
      input.offlineRaisedCents,
      input.capacity,
      input.accent,
      input.position,
    ],
  );
}

export async function updateProject(originalSlug: string, input: ProjectInput): Promise<void> {
  const db = await getDb();
  const rows = await db.query("SELECT 1 FROM projects WHERE slug = $1", [originalSlug]);
  if (rows.length === 0) throw new AdminError("That project no longer exists.", 404);

  await db.query(
    `UPDATE projects SET
       slug = $1, name = $2, city = $3, country = $4, summary = $5, story = $6,
       status = $7, goal_cents = $8, offline_raised_cents = $9, capacity = $10,
       accent = $11, position = $12
     WHERE slug = $13`,
    [
      input.slug,
      input.name,
      input.city,
      input.country,
      input.summary,
      input.story,
      input.status,
      input.goalCents,
      input.offlineRaisedCents,
      input.capacity,
      input.accent,
      input.position,
      originalSlug,
    ],
  );
}

export async function addProjectCost(
  slug: string,
  input: z.infer<typeof costSchema>,
): Promise<void> {
  const db = await getDb();
  const rows = await db.query<{ id: string }>("SELECT id FROM projects WHERE slug = $1", [slug]);
  if (rows.length === 0) throw new AdminError("That project no longer exists.", 404);

  await db.query(
    "INSERT INTO project_costs (project_id, label, detail, unit_cost_cents, position) VALUES ($1,$2,$3,$4,$5)",
    [rows[0].id, input.label, input.detail, input.unitCostCents, input.position],
  );
}

export async function deleteProjectCost(id: string): Promise<void> {
  const db = await getDb();
  await db.query("DELETE FROM project_costs WHERE id = $1", [id]);
}

export async function postProjectUpdate(
  slug: string,
  input: z.infer<typeof updateSchema>,
): Promise<void> {
  const db = await getDb();
  const rows = await db.query<{ id: string }>("SELECT id FROM projects WHERE slug = $1", [slug]);
  if (rows.length === 0) throw new AdminError("That project no longer exists.", 404);

  await db.query("INSERT INTO project_updates (project_id, title, body) VALUES ($1,$2,$3)", [
    rows[0].id,
    input.title,
    input.body,
  ]);
}

export interface AdminDonationRow {
  reference: string;
  createdAt: string;
  completedAt: string | null;
  amountCents: number;
  currency: string;
  status: string;
  frequency: string;
  intent: string;
  provider: string;
  donorName: string | null;
  donorEmail: string;
  anonymous: boolean;
  dedication: string | null;
  projectName: string | null;
  method: string;
  cancelledAt: string | null;
  receiptSentAt: string | null;
  /**
   * Monthly gifts only. Staff need it to cancel on behalf of a donor who has
   * lost their receipt — deliberately kept out of the CSV export, which gets
   * passed around outside the office.
   */
  manageToken: string | null;
}

export interface DonationFilters {
  status?: string;
  projectSlug?: string;
  limit?: number;
}

export async function listDonationsForAdmin(
  filters: DonationFilters = {},
): Promise<AdminDonationRow[]> {
  const db = await getDb();
  const conditions: string[] = [];
  const params: unknown[] = [];

  if (filters.status) {
    params.push(filters.status);
    conditions.push(`d.status = $${params.length}`);
  }
  if (filters.projectSlug) {
    params.push(filters.projectSlug);
    conditions.push(`p.slug = $${params.length}`);
  }
  params.push(filters.limit ?? 200);

  const rows = await db.query<{
    reference: string;
    created_at: string | Date;
    completed_at: string | Date | null;
    amount_cents: string | number;
    currency: string;
    status: string;
    frequency: string;
    intent: string;
    provider: string;
    donor_name: string | null;
    donor_email: string;
    anonymous: boolean;
    dedication: string | null;
    project_name: string | null;
    method: string | null;
    cancelled_at: string | Date | null;
    receipt_sent_at: string | Date | null;
    manage_token: string | null;
  }>(
    `SELECT d.reference, d.created_at, d.completed_at, d.amount_cents, d.currency, d.status,
            d.frequency, d.intent, d.provider, d.donor_name, d.donor_email, d.anonymous,
            d.dedication, d.method, d.cancelled_at, d.receipt_sent_at, d.manage_token, p.name AS project_name
     FROM donations d LEFT JOIN projects p ON p.id = d.project_id
     ${conditions.length > 0 ? `WHERE ${conditions.join(" AND ")}` : ""}
     ORDER BY d.created_at DESC
     LIMIT $${params.length}`,
    params,
  );

  return rows.map((r) => ({
    reference: r.reference,
    createdAt: new Date(r.created_at).toISOString(),
    completedAt: r.completed_at ? new Date(r.completed_at).toISOString() : null,
    amountCents: toCents(r.amount_cents),
    currency: r.currency,
    status: r.status,
    frequency: r.frequency,
    intent: r.intent,
    provider: r.provider,
    donorName: r.donor_name,
    donorEmail: r.donor_email,
    anonymous: r.anonymous,
    dedication: r.dedication,
    projectName: r.project_name,
    method: r.method ?? "card",
    cancelledAt: r.cancelled_at ? new Date(r.cancelled_at).toISOString() : null,
    receiptSentAt: r.receipt_sent_at ? new Date(r.receipt_sent_at).toISOString() : null,
    manageToken: r.manage_token,
  }));
}

/** Spreadsheet export for the accounts, newest first. */
export function donationsToCsv(rows: AdminDonationRow[]): string {
  const header = [
    "reference",
    "created_at",
    "completed_at",
    "status",
    "amount",
    "currency",
    "frequency",
    "intent",
    "provider",
    "project",
    "donor_name",
    "donor_email",
    "anonymous",
    "dedication",
    "cancelled_at",
    "receipt_sent_at",
  ];
  const lines = rows.map((r) =>
    [
      r.reference,
      r.createdAt,
      r.completedAt ?? "",
      r.status,
      (r.amountCents / 100).toFixed(2),
      r.currency,
      r.frequency,
      r.intent,
      r.provider,
      r.projectName ?? "",
      r.donorName ?? "",
      r.donorEmail,
      r.anonymous ? "yes" : "no",
      r.dedication ?? "",
      r.cancelledAt ?? "",
      r.receiptSentAt ?? "",
    ]
      .map(csvCell)
      .join(","),
  );
  return [header.join(","), ...lines].join("\n");
}

/**
 * Quote every cell and neutralise leading =, +, - and @ so a donor-supplied
 * name cannot execute as a formula when the export is opened in a spreadsheet.
 */
function csvCell(value: string): string {
  const guarded = /^[=+\-@]/.test(value) ? `'${value}` : value;
  return `"${guarded.replace(/"/g, '""')}"`;
}

export interface AdminStats {
  pendingCount: number;
  completedCount: number;
  failedCount: number;
  monthlyActiveCount: number;
  settledCents: number;
  last30DaysCents: number;
  failedEmailCount: number;
}

export async function getAdminStats(): Promise<AdminStats> {
  const db = await getDb();
  const [donations] = await db.query<{
    pending: string | number;
    completed: string | number;
    failed: string | number;
    monthly_active: string | number;
    settled_cents: string | number | null;
    last_30: string | number | null;
  }>(`
    SELECT COUNT(*) FILTER (WHERE status = 'pending')   AS pending,
           COUNT(*) FILTER (WHERE status = 'completed') AS completed,
           COUNT(*) FILTER (WHERE status = 'failed')    AS failed,
           COUNT(*) FILTER (WHERE frequency = 'monthly' AND status = 'completed' AND cancelled_at IS NULL) AS monthly_active,
           SUM(COALESCE(base_amount_cents, amount_cents)) FILTER (WHERE status = 'completed') AS settled_cents,
           SUM(COALESCE(base_amount_cents, amount_cents)) FILTER (WHERE status = 'completed' AND completed_at > now() - interval '30 days') AS last_30
    FROM donations
  `);
  const [emails] = await db.query<{ failed: string | number }>(
    "SELECT COUNT(*) AS failed FROM email_log WHERE status = 'failed'",
  );

  return {
    pendingCount: Number(donations?.pending ?? 0),
    completedCount: Number(donations?.completed ?? 0),
    failedCount: Number(donations?.failed ?? 0),
    monthlyActiveCount: Number(donations?.monthly_active ?? 0),
    settledCents: toCents(donations?.settled_cents),
    last30DaysCents: toCents(donations?.last_30),
    failedEmailCount: Number(emails?.failed ?? 0),
  };
}
