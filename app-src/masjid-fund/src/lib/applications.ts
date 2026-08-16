import { getDb } from "@/db";
import {
  ApplicationError,
  APPLICATION_CURRENCIES,
  STATUS_LABELS,
  parseApplicationInput,
  type ApplicationInput,
  type ApplicationStatus,
  type LandOwnership,
} from "./application";
import { sendApplicationReceived, sendApplicationStatus } from "./email";
import {
  FILE_KINDS,
  FileError,
  MAX_FILES_PER_APPLICATION,
  type FileKind,
  type StoredFile,
} from "./files";
import { toCents } from "./money";
import { APPLICATION_LIMITS, countRecent, hashIp } from "./rate-limit";
import { newManageToken } from "./reference";

export * from "./application";

/**
 * Applications from communities asking to have a masjid funded.
 *
 * Nothing an applicant submits is public. Staff review the documents, then
 * either publish an approved application as a fundable project or return it
 * with a reason. Every state change is written to application_events, so the
 * decision trail survives staff turnover.
 */

export interface ApplicationDocument {
  id: string;
  kind: FileKind;
  filename: string;
  contentType: string;
  byteSize: number;
  uploadedAt: string;
}

export interface ApplicationEvent {
  id: string;
  actor: string;
  action: string;
  note: string | null;
  createdAt: string;
}

export interface Application extends ApplicationInput {
  id: string;
  reference: string;
  status: ApplicationStatus;
  statusNote: string | null;
  manageToken: string;
  projectId: string | null;
  projectSlug: string | null;
  createdAt: string;
  decidedAt: string | null;
  documents: ApplicationDocument[];
}

const REQUIRED_KINDS: FileKind[] = ["title_deed", "drawings", "boq"];

export async function submitApplication(
  raw: unknown,
  files: { kind: FileKind; file: StoredFile }[],
  meta: { ip?: string | null } = {},
): Promise<{ reference: string; statusToken: string }> {
  const input = parseApplicationInput(raw);

  const missing = REQUIRED_KINDS.filter((kind) => !files.some((f) => f.kind === kind));
  if (missing.length > 0) {
    const names = missing.map(
      (kind) => FILE_KINDS.find((k) => k.kind === kind)?.label.toLowerCase() ?? kind,
    );
    throw new FileError(
      `Please attach the ${listPhrase(names)} before submitting.`,
    );
  }
  if (files.length > MAX_FILES_PER_APPLICATION) {
    throw new FileError(`Please attach no more than ${MAX_FILES_PER_APPLICATION} files.`);
  }

  const ipHash = meta.ip ? hashIp(meta.ip) : null;
  await assertNotFlooding(input.contactEmail, ipHash);

  const db = await getDb();
  const reference = newApplicationReference();
  const manageToken = newManageToken();

  const rows = await db.query<{ id: string }>(
    `INSERT INTO applications
       (reference, masjid_name, city, country, location_note, congregation_now, capacity_planned,
        estimated_cost_cents, already_raised_cents, currency, land_title_number, land_ownership,
        titled_to_trust, trust_name, trust_registration, contact_name, contact_role, contact_email,
        contact_phone, story, manage_token, ip_hash)
     VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20,$21,$22)
     RETURNING id`,
    [
      reference,
      input.masjidName,
      input.city,
      input.country,
      input.locationNote || null,
      input.congregationNow,
      input.capacityPlanned,
      input.estimatedCostCents,
      input.alreadyRaisedCents,
      input.currency,
      input.landTitleNumber,
      input.landOwnership,
      input.titledToTrust,
      input.trustName || null,
      input.trustRegistration || null,
      input.contactName,
      input.contactRole,
      input.contactEmail,
      input.contactPhone,
      input.story,
      manageToken,
      ipHash,
    ],
  );
  const applicationId = rows[0].id;

  for (const { kind, file } of files) {
    await db.query(
      `INSERT INTO application_documents (application_id, kind, filename, content_type, byte_size, data)
       VALUES ($1,$2,$3,$4,$5,$6)`,
      [applicationId, kind, file.filename, file.contentType, file.bytes.byteLength, file.bytes],
    );
  }

  await recordEvent(applicationId, "applicant", "submitted", null);
  await sendApplicationReceived({
    reference,
    masjidName: input.masjidName,
    contactName: input.contactName,
    contactEmail: input.contactEmail,
    manageToken,
  });
  return { reference, statusToken: manageToken };
}

export async function getApplicationByToken(token: string): Promise<Application | null> {
  return findApplication("a.manage_token = $1", [token]);
}

export async function getApplicationById(id: string): Promise<Application | null> {
  return findApplication("a.id = $1", [id]);
}

export async function listApplications(status?: string): Promise<Application[]> {
  const db = await getDb();
  const rows = await db.query<ApplicationRow>(
    `SELECT a.*, p.slug AS project_slug FROM applications a
     LEFT JOIN projects p ON p.id = a.project_id
     ${status ? "WHERE a.status = $1" : ""}
     ORDER BY a.created_at DESC
     LIMIT 200`,
    status ? [status] : [],
  );
  return rows.map((row) => toApplication(row, []));
}

export async function listApplicationEvents(id: string): Promise<ApplicationEvent[]> {
  const db = await getDb();
  const rows = await db.query<{
    id: string;
    actor: string;
    action: string;
    note: string | null;
    created_at: string | Date;
  }>(
    "SELECT id, actor, action, note, created_at FROM application_events WHERE application_id = $1 ORDER BY created_at",
    [id],
  );
  return rows.map((r) => ({
    id: r.id,
    actor: r.actor,
    action: r.action,
    note: r.note,
    createdAt: new Date(r.created_at).toISOString(),
  }));
}

/** Document bytes, for the staff-only download route. */
export async function getDocumentBytes(
  documentId: string,
): Promise<{ filename: string; contentType: string; bytes: Uint8Array } | null> {
  const db = await getDb();
  const rows = await db.query<{ filename: string; content_type: string; data: Uint8Array }>(
    "SELECT filename, content_type, data FROM application_documents WHERE id = $1",
    [documentId],
  );
  if (rows.length === 0) return null;
  return {
    filename: rows[0].filename,
    contentType: rows[0].content_type,
    bytes: new Uint8Array(rows[0].data),
  };
}

/**
 * Move an application along. `note` reaches the applicant on their status page
 * and in the email, so it is written for them, not for internal shorthand.
 */
export async function setApplicationStatus(
  id: string,
  status: ApplicationStatus,
  note: string | null,
  actor: string,
): Promise<Application | null> {
  const application = await getApplicationById(id);
  if (!application) throw new ApplicationError("That application no longer exists.", 404);
  if (status === "approved" && !application.projectId) {
    throw new ApplicationError(
      "Publish the project first — approving is what happens when the project goes live.",
      409,
    );
  }

  const db = await getDb();
  const decided = status === "approved" || status === "rejected";
  await db.query(
    `UPDATE applications
     SET status = $1, status_note = $2, decided_at = CASE WHEN $3 THEN now() ELSE decided_at END
     WHERE id = $4`,
    [status, note, decided, id],
  );
  await recordEvent(id, actor, status, note);

  const updated = await getApplicationById(id);
  // "In review" is an internal step; the applicant hears about the rest.
  if (updated && status !== "in_review") {
    await sendApplicationStatus(
      {
        reference: updated.reference,
        masjidName: updated.masjidName,
        contactName: updated.contactName,
        contactEmail: updated.contactEmail,
        status: updated.status,
        manageToken: updated.manageToken,
        projectSlug: updated.projectSlug,
      },
      STATUS_LABELS[status],
      note,
    );
  }
  return updated;
}

/**
 * Turn an approved application into a live project. The project is created
 * from staff-checked values rather than straight from the form, and the
 * application is linked to it so the paperwork stays findable afterwards.
 */
export async function linkApplicationToProject(
  id: string,
  projectId: string,
  actor: string,
): Promise<void> {
  const db = await getDb();
  await db.query("UPDATE applications SET project_id = $1 WHERE id = $2", [projectId, id]);
  await recordEvent(id, actor, "published", null);
}

async function recordEvent(
  applicationId: string,
  actor: string,
  action: string,
  note: string | null,
): Promise<void> {
  const db = await getDb();
  await db.query(
    "INSERT INTO application_events (application_id, actor, action, note) VALUES ($1,$2,$3,$4)",
    [applicationId, actor, action, note],
  );
}

async function assertNotFlooding(email: string, ipHash: string | null): Promise<void> {
  const byEmail = await countRecent(
    "applications",
    "contact_email",
    email,
    APPLICATION_LIMITS.perEmail.minutes,
  );
  if (byEmail >= APPLICATION_LIMITS.perEmail.max) {
    throw new ApplicationError(
      "We already have several applications from this address today. Email us if you need to add anything to them.",
      429,
    );
  }

  if (!ipHash) return;
  const byIp = await countRecent(
    "applications",
    "ip_hash",
    ipHash,
    APPLICATION_LIMITS.perIp.minutes,
  );
  if (byIp >= APPLICATION_LIMITS.perIp.max) {
    throw new ApplicationError("Too many applications from this connection today.", 429);
  }
}

/** "a, b and c" — reads better than a bare comma list in an error message. */
function listPhrase(items: string[]): string {
  if (items.length <= 1) return items[0] ?? "";
  return `${items.slice(0, -1).join(", ")} and ${items[items.length - 1]}`;
}

function newApplicationReference(): string {
  return `MA-${newManageToken().replace(/[^A-Z0-9]/gi, "").toUpperCase().slice(0, 8)}`;
}

interface ApplicationRow {
  id: string;
  reference: string;
  status: string;
  masjid_name: string;
  city: string;
  country: string;
  location_note: string | null;
  congregation_now: number;
  capacity_planned: number;
  estimated_cost_cents: string | number;
  already_raised_cents: string | number;
  currency: string;
  land_title_number: string;
  land_ownership: string;
  titled_to_trust: boolean;
  trust_name: string | null;
  trust_registration: string | null;
  contact_name: string;
  contact_role: string;
  contact_email: string;
  contact_phone: string;
  story: string;
  status_note: string | null;
  manage_token: string;
  project_id: string | null;
  project_slug: string | null;
  created_at: string | Date;
  decided_at: string | Date | null;
}

async function findApplication(where: string, params: unknown[]): Promise<Application | null> {
  const db = await getDb();
  const rows = await db.query<ApplicationRow>(
    `SELECT a.*, p.slug AS project_slug FROM applications a
     LEFT JOIN projects p ON p.id = a.project_id
     WHERE ${where}`,
    params,
  );
  if (rows.length === 0) return null;

  const documents = await db.query<{
    id: string;
    kind: string;
    filename: string;
    content_type: string;
    byte_size: number;
    uploaded_at: string | Date;
  }>(
    `SELECT id, kind, filename, content_type, byte_size, uploaded_at
     FROM application_documents WHERE application_id = $1 ORDER BY uploaded_at`,
    [rows[0].id],
  );

  return toApplication(
    rows[0],
    documents.map((d) => ({
      id: d.id,
      kind: d.kind as FileKind,
      filename: d.filename,
      contentType: d.content_type,
      byteSize: Number(d.byte_size),
      uploadedAt: new Date(d.uploaded_at).toISOString(),
    })),
  );
}

function toApplication(row: ApplicationRow, documents: ApplicationDocument[]): Application {
  return {
    id: row.id,
    reference: row.reference,
    status: row.status as ApplicationStatus,
    masjidName: row.masjid_name,
    city: row.city,
    country: row.country,
    locationNote: row.location_note ?? "",
    congregationNow: row.congregation_now,
    capacityPlanned: row.capacity_planned,
    estimatedCostCents: toCents(row.estimated_cost_cents),
    alreadyRaisedCents: toCents(row.already_raised_cents),
    currency: row.currency as (typeof APPLICATION_CURRENCIES)[number],
    landTitleNumber: row.land_title_number,
    landOwnership: row.land_ownership as LandOwnership,
    titledToTrust: row.titled_to_trust,
    trustName: row.trust_name ?? "",
    trustRegistration: row.trust_registration ?? "",
    contactName: row.contact_name,
    contactRole: row.contact_role,
    contactEmail: row.contact_email,
    contactPhone: row.contact_phone,
    story: row.story,
    consentTruthful: true,
    consentPublish: true,
    statusNote: row.status_note,
    manageToken: row.manage_token,
    projectId: row.project_id,
    projectSlug: row.project_slug,
    createdAt: new Date(row.created_at).toISOString(),
    decidedAt: row.decided_at ? new Date(row.decided_at).toISOString() : null,
    documents,
  };
}
