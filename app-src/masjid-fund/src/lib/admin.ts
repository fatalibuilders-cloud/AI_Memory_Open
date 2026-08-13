import { randomBytes, scrypt as scryptCallback, timingSafeEqual } from "crypto";
import { promisify } from "util";
import { cookies } from "next/headers";
import { getDb } from "@/db";

/**
 * Staff authentication for the /admin screens.
 *
 * Credentials come from the environment rather than a users table: one shared
 * operator login is enough for a small programme team, and it keeps password
 * resets out of the app. Sessions live in the database so a logout, or a
 * password change at deploy time, ends them everywhere.
 */

const scrypt = promisify(scryptCallback) as (
  password: string,
  salt: Buffer,
  keylen: number,
) => Promise<Buffer>;

export const ADMIN_COOKIE = "mf_admin";
const SESSION_HOURS = 12;
const KEY_LENGTH = 64;

/** Dev-only credentials when no hash is configured. Never active in production. */
const DEV_EMAIL = "admin@localhost";
const DEV_PASSWORD = "masjidfund-dev";

export class AdminError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

/** `scrypt$<salt base64>$<key base64>` — see scripts/hash-password.mjs. */
export async function hashPassword(password: string): Promise<string> {
  const salt = randomBytes(16);
  const key = await scrypt(password, salt, KEY_LENGTH);
  return `scrypt$${salt.toString("base64")}$${key.toString("base64")}`;
}

export async function verifyPassword(password: string, stored: string): Promise<boolean> {
  const [scheme, saltB64, keyB64] = stored.split("$");
  if (scheme !== "scrypt" || !saltB64 || !keyB64) return false;
  const expected = Buffer.from(keyB64, "base64");
  const actual = await scrypt(password, Buffer.from(saltB64, "base64"), expected.length);
  return expected.length === actual.length && timingSafeEqual(expected, actual);
}

/** True when this deployment has real credentials configured. */
export function adminConfigured(): boolean {
  return Boolean(process.env.ADMIN_EMAIL && process.env.ADMIN_PASSWORD_HASH);
}

function devLoginAllowed(): boolean {
  return !adminConfigured() && process.env.NODE_ENV !== "production";
}

/** Explains the login options on the sign-in screen. */
export function loginMode(): "configured" | "dev" | "disabled" {
  if (adminConfigured()) return "configured";
  return devLoginAllowed() ? "dev" : "disabled";
}

export async function adminLogin(emailRaw: string, password: string): Promise<string> {
  const email = emailRaw.trim().toLowerCase();
  const invalid = new AdminError("Email or password is incorrect.", 401);

  if (adminConfigured()) {
    if (email !== process.env.ADMIN_EMAIL!.trim().toLowerCase()) throw invalid;
    if (!(await verifyPassword(password, process.env.ADMIN_PASSWORD_HASH!))) throw invalid;
  } else if (devLoginAllowed()) {
    if (email !== DEV_EMAIL || password !== DEV_PASSWORD) throw invalid;
  } else {
    throw new AdminError(
      "Admin access is not configured. Set ADMIN_EMAIL and ADMIN_PASSWORD_HASH.",
      503,
    );
  }

  const token = randomBytes(32).toString("base64url");
  const expiresAt = new Date(Date.now() + SESSION_HOURS * 60 * 60 * 1000);
  const db = await getDb();
  await db.query("INSERT INTO admin_sessions (token, email, expires_at) VALUES ($1, $2, $3)", [
    token,
    email,
    expiresAt.toISOString(),
  ]);

  const jar = await cookies();
  jar.set(ADMIN_COOKIE, token, {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    expires: expiresAt,
  });
  return token;
}

export async function adminLogout(): Promise<void> {
  const jar = await cookies();
  const token = jar.get(ADMIN_COOKIE)?.value;
  if (token) {
    const db = await getDb();
    await db.query("DELETE FROM admin_sessions WHERE token = $1", [token]);
  }
  jar.delete(ADMIN_COOKIE);
}

/** Current staff session, or null. Expired rows are treated as absent. */
export async function getAdminSession(): Promise<{ email: string } | null> {
  const jar = await cookies();
  const token = jar.get(ADMIN_COOKIE)?.value;
  if (!token) return null;

  const db = await getDb();
  const rows = await db.query<{ email: string }>(
    "SELECT email FROM admin_sessions WHERE token = $1 AND expires_at > now()",
    [token],
  );
  return rows.length > 0 ? { email: rows[0].email } : null;
}

/**
 * Guard for admin pages and actions. Throws rather than redirecting so a
 * server action cannot silently continue when the session has lapsed.
 */
export async function requireAdmin(): Promise<{ email: string }> {
  const session = await getAdminSession();
  if (!session) throw new AdminError("Sign in to continue.", 401);
  return session;
}
