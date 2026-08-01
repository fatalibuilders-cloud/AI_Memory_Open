import { getDb } from "@/db";
import { toCents } from "./money";

/**
 * Read model for masjid building projects.
 *
 * "Raised" is always the sum of completed donations plus the offline total
 * (bank transfers, community collections) recorded on the project itself —
 * computed in SQL so no cached counter can drift out of step with the ledger.
 */

export type ProjectStatus = "planning" | "building" | "completed";

export interface Project {
  id: string;
  slug: string;
  name: string;
  city: string;
  country: string;
  summary: string;
  story: string;
  status: ProjectStatus;
  goalCents: number;
  raisedCents: number;
  donorCount: number;
  capacity: number;
  zakatEligible: boolean;
  accent: string;
}

export interface ProjectCost {
  id: string;
  label: string;
  detail: string;
  unitCostCents: number;
}

export interface ProjectUpdate {
  id: string;
  title: string;
  body: string;
  postedAt: string;
}

export interface ProjectDetail extends Project {
  costs: ProjectCost[];
  updates: ProjectUpdate[];
}

export interface FundStats {
  raisedCents: number;
  donorCount: number;
  projectsCompleted: number;
  projectsActive: number;
  worshippersServed: number;
}

export interface RecentDonation {
  name: string;
  amountCents: number;
  projectName: string | null;
  dedication: string | null;
  createdAt: string;
}

interface ProjectRow {
  id: string;
  slug: string;
  name: string;
  city: string;
  country: string;
  summary: string;
  story: string;
  status: string;
  goal_cents: string | number;
  offline_raised_cents: string | number;
  donated_cents: string | number | null;
  donor_count: string | number | null;
  capacity: number;
  zakat_eligible: boolean;
  accent: string;
}

const PROJECT_SELECT = `
  SELECT p.*,
         COALESCE(d.donated_cents, 0) AS donated_cents,
         COALESCE(d.donor_count, 0)   AS donor_count
  FROM projects p
  LEFT JOIN (
    SELECT project_id,
           SUM(amount_cents) AS donated_cents,
           COUNT(*)          AS donor_count
    FROM donations
    WHERE status = 'completed'
    GROUP BY project_id
  ) d ON d.project_id = p.id
`;

export async function listProjects(): Promise<Project[]> {
  const db = await getDb();
  const rows = await db.query<ProjectRow>(`${PROJECT_SELECT} ORDER BY p.position, p.name`);
  return rows.map(toProject);
}

export async function getProjectBySlug(slug: string): Promise<ProjectDetail | null> {
  const db = await getDb();
  const rows = await db.query<ProjectRow>(`${PROJECT_SELECT} WHERE p.slug = $1`, [slug]);
  if (rows.length === 0) return null;
  const project = toProject(rows[0]);

  const costs = await db.query<{
    id: string;
    label: string;
    detail: string;
    unit_cost_cents: string | number;
  }>(
    "SELECT id, label, detail, unit_cost_cents FROM project_costs WHERE project_id = $1 ORDER BY position",
    [project.id],
  );
  const updates = await db.query<{
    id: string;
    title: string;
    body: string;
    posted_at: string | Date;
  }>(
    "SELECT id, title, body, posted_at FROM project_updates WHERE project_id = $1 ORDER BY posted_at DESC",
    [project.id],
  );

  return {
    ...project,
    costs: costs.map((c) => ({
      id: c.id,
      label: c.label,
      detail: c.detail,
      unitCostCents: toCents(c.unit_cost_cents),
    })),
    updates: updates.map((u) => ({
      id: u.id,
      title: u.title,
      body: u.body,
      postedAt: new Date(u.posted_at).toISOString(),
    })),
  };
}

export async function getFundStats(): Promise<FundStats> {
  const db = await getDb();
  const [totals] = await db.query<{
    donated_cents: string | number | null;
    donor_count: string | number | null;
  }>(
    "SELECT SUM(amount_cents) AS donated_cents, COUNT(*) AS donor_count FROM donations WHERE status = 'completed'",
  );
  const [projects] = await db.query<{
    offline_cents: string | number | null;
    completed: string | number;
    active: string | number;
    worshippers: string | number | null;
  }>(`
    SELECT SUM(offline_raised_cents) AS offline_cents,
           COUNT(*) FILTER (WHERE status = 'completed') AS completed,
           COUNT(*) FILTER (WHERE status <> 'completed') AS active,
           SUM(capacity) AS worshippers
    FROM projects
  `);

  return {
    raisedCents: toCents(totals?.donated_cents) + toCents(projects?.offline_cents),
    donorCount: Number(totals?.donor_count ?? 0),
    projectsCompleted: Number(projects?.completed ?? 0),
    projectsActive: Number(projects?.active ?? 0),
    worshippersServed: Number(projects?.worshippers ?? 0),
  };
}

export async function listRecentDonations(limit = 6): Promise<RecentDonation[]> {
  const db = await getDb();
  const rows = await db.query<{
    donor_name: string | null;
    anonymous: boolean;
    amount_cents: string | number;
    project_name: string | null;
    dedication: string | null;
    created_at: string | Date;
  }>(
    `SELECT d.donor_name, d.anonymous, d.amount_cents, d.dedication, d.created_at, p.name AS project_name
     FROM donations d
     LEFT JOIN projects p ON p.id = d.project_id
     WHERE d.status = 'completed'
     ORDER BY d.completed_at DESC NULLS LAST, d.created_at DESC
     LIMIT $1`,
    [limit],
  );
  return rows.map((r) => ({
    name: r.anonymous || !r.donor_name ? "Anonymous" : r.donor_name,
    amountCents: toCents(r.amount_cents),
    projectName: r.project_name,
    dedication: r.dedication,
    createdAt: new Date(r.created_at).toISOString(),
  }));
}

function toProject(row: ProjectRow): Project {
  return {
    id: row.id,
    slug: row.slug,
    name: row.name,
    city: row.city,
    country: row.country,
    summary: row.summary,
    story: row.story,
    status: row.status as ProjectStatus,
    goalCents: toCents(row.goal_cents),
    raisedCents: toCents(row.offline_raised_cents) + toCents(row.donated_cents),
    donorCount: Number(row.donor_count ?? 0),
    capacity: row.capacity,
    zakatEligible: row.zakat_eligible,
    accent: row.accent,
  };
}
