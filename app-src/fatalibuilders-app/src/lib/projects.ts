// Server-side only — project CRUD with ownership enforced on every query.
import { getDb } from "@/db";
import { AuthError } from "./auth";
import {
  projectDataSchema,
  projectDraftSchema,
  type ProjectDraft,
  type ProjectRecord,
} from "./project-schema";

interface Row {
  id: string;
  name: string;
  status: string;
  data: unknown;
  created_at: string;
  updated_at: string;
}

export async function createProject(userId: string, name = "Untitled project"): Promise<ProjectRecord> {
  const db = await getDb();
  const rows = await db.query<Row>(
    "INSERT INTO projects (user_id, name) VALUES ($1, $2) RETURNING id, name, status, data, created_at, updated_at",
    [userId, name.trim() || "Untitled project"],
  );
  return toRecord(rows[0]);
}

export async function listProjects(userId: string): Promise<ProjectRecord[]> {
  const db = await getDb();
  const rows = await db.query<Row>(
    "SELECT id, name, status, data, created_at, updated_at FROM projects WHERE user_id = $1 ORDER BY updated_at DESC",
    [userId],
  );
  return rows.map(toRecord);
}

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export async function getProject(userId: string, projectId: string): Promise<ProjectRecord> {
  if (!UUID_RE.test(projectId)) throw new AuthError("Project not found.", 404);
  const db = await getDb();
  const rows = await db.query<Row>(
    "SELECT id, name, status, data, created_at, updated_at FROM projects WHERE user_id = $1 AND id = $2",
    [userId, projectId],
  );
  if (rows.length === 0) throw new AuthError("Project not found.", 404);
  return toRecord(rows[0]);
}

export async function updateProject(
  userId: string,
  projectId: string,
  patch: { name?: string; data?: unknown; status?: "draft" | "complete" },
): Promise<ProjectRecord> {
  const current = await getProject(userId, projectId);

  const name = patch.name !== undefined ? patch.name.trim() || current.name : current.name;
  let data: ProjectDraft = current.data;
  if (patch.data !== undefined) {
    const parsed = projectDraftSchema.safeParse(patch.data);
    if (!parsed.success) {
      throw new AuthError(parsed.error.issues[0]?.message ?? "Invalid project data", 400);
    }
    data = { ...current.data, ...parsed.data };
  }

  const status = patch.status ?? current.status;
  if (status === "complete") {
    const full = projectDataSchema.safeParse(data);
    if (!full.success) {
      throw new AuthError(
        `Cannot finish yet: ${full.error.issues[0]?.message ?? "some details are missing"}`,
        400,
      );
    }
    data = full.data;
  }

  const db = await getDb();
  const rows = await db.query<Row>(
    `UPDATE projects SET name = $3, status = $4, data = $5, updated_at = now()
     WHERE user_id = $1 AND id = $2
     RETURNING id, name, status, data, created_at, updated_at`,
    [userId, projectId, name, status, JSON.stringify(data)],
  );
  return toRecord(rows[0]);
}

function toRecord(row: Row): ProjectRecord {
  const data = typeof row.data === "string" ? JSON.parse(row.data) : row.data;
  return {
    id: row.id,
    name: row.name,
    status: row.status as ProjectRecord["status"],
    data: (data ?? {}) as ProjectDraft,
    createdAt: String(row.created_at),
    updatedAt: String(row.updated_at),
  };
}
