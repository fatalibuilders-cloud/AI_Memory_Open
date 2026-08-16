import { createHash } from "crypto";
import { getDb } from "@/db";

/**
 * Database-backed throttling.
 *
 * Counting rows we already store beats an in-memory counter here: it survives
 * restarts, and on a serverless host every instance sees the same numbers.
 * The volumes involved — a donation form and an application form — are far too
 * low for the extra query to matter.
 */

/** Salted so no table holds a reversible IP address. */
export function hashIp(ip: string): string {
  const salt = process.env.IP_HASH_SALT ?? "masjid-fund";
  return createHash("sha256").update(`${salt}:${ip}`).digest("hex").slice(0, 32);
}

/** The caller's address, as far as the proxy in front of us reports it. */
export function clientIp(headers: Headers): string | null {
  const forwarded = headers.get("x-forwarded-for")?.split(",")[0]?.trim();
  return forwarded || headers.get("x-real-ip") || null;
}

/**
 * How many rows in `table` match `column = value` within the last `minutes`.
 * Table and column names are supplied by call sites, never by request data.
 */
export async function countRecent(
  table: "donations" | "applications",
  column: "ip_hash" | "donor_email" | "contact_email",
  value: string,
  minutes: number,
): Promise<number> {
  const db = await getDb();
  const [row] = await db.query<{ count: string | number }>(
    `SELECT COUNT(*) AS count FROM ${table}
     WHERE ${column} = $1 AND created_at > now() - ($2 || ' minutes')::interval`,
    [value, String(minutes)],
  );
  return Number(row?.count ?? 0);
}

/**
 * Card testing looks like a burst of small donations from one source, so the
 * limits are tight on attempts per network and per email address. A genuine
 * donor giving to three projects in an evening stays well inside them.
 */
export const DONATION_LIMITS = {
  perIp: { max: 12, minutes: 60 },
  perEmail: { max: 6, minutes: 60 },
};

export const APPLICATION_LIMITS = {
  perIp: { max: 10, minutes: 60 * 24 },
  perEmail: { max: 3, minutes: 60 * 24 },
};
