// Server-side only — imported from API route handlers and server components.
import { randomBytes } from "crypto";
import argon2 from "argon2";
import { z } from "zod";
import { getDb } from "@/db";

const SESSION_DAYS = 30;
export const SESSION_COOKIE = "fb_session";

export const credentialsSchema = z.object({
  email: z.string().trim().toLowerCase().email("Enter a valid email address"),
  password: z.string().min(8, "Password must be at least 8 characters"),
});

export interface SafeUser {
  id: string;
  email: string;
  name: string | null;
  lifetimeAccess: boolean;
}

export class AuthError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

export async function signup(emailRaw: string, passwordRaw: string): Promise<SafeUser> {
  const { email, password } = parse(emailRaw, passwordRaw);
  const db = await getDb();
  const existing = await db.query("SELECT id FROM users WHERE email = $1", [email]);
  if (existing.length > 0) {
    throw new AuthError("An account with this email already exists. Try signing in.", 409);
  }
  const passwordHash = await argon2.hash(password);
  const rows = await db.query<{
    id: string;
    email: string;
    name: string | null;
    lifetime_access: boolean;
  }>(
    "INSERT INTO users (email, password_hash) VALUES ($1, $2) RETURNING id, email, name, lifetime_access",
    [email, passwordHash],
  );
  return toSafeUser(rows[0]);
}

export async function login(emailRaw: string, passwordRaw: string): Promise<SafeUser> {
  const { email, password } = parse(emailRaw, passwordRaw);
  const db = await getDb();
  const rows = await db.query<{
    id: string;
    email: string;
    name: string | null;
    lifetime_access: boolean;
    password_hash: string;
  }>("SELECT id, email, name, lifetime_access, password_hash FROM users WHERE email = $1", [email]);
  const invalid = new AuthError("Email or password is incorrect.", 401);
  if (rows.length === 0) throw invalid;
  const ok = await argon2.verify(rows[0].password_hash, password);
  if (!ok) throw invalid;
  return toSafeUser(rows[0]);
}

export async function createSession(userId: string): Promise<{ token: string; expiresAt: Date }> {
  const token = randomBytes(32).toString("hex");
  const expiresAt = new Date(Date.now() + SESSION_DAYS * 24 * 60 * 60 * 1000);
  const db = await getDb();
  await db.query("INSERT INTO sessions (token, user_id, expires_at) VALUES ($1, $2, $3)", [
    token,
    userId,
    expiresAt.toISOString(),
  ]);
  return { token, expiresAt };
}

export async function deleteSession(token: string): Promise<void> {
  const db = await getDb();
  await db.query("DELETE FROM sessions WHERE token = $1", [token]);
}

export async function getUserBySession(token: string | undefined): Promise<SafeUser | null> {
  if (!token) return null;
  const db = await getDb();
  const rows = await db.query<{
    id: string;
    email: string;
    name: string | null;
    lifetime_access: boolean;
  }>(
    `SELECT u.id, u.email, u.name, u.lifetime_access
     FROM sessions s JOIN users u ON u.id = s.user_id
     WHERE s.token = $1 AND s.expires_at > now()`,
    [token],
  );
  return rows.length > 0 ? toSafeUser(rows[0]) : null;
}

function parse(email: string, password: string): { email: string; password: string } {
  const result = credentialsSchema.safeParse({ email, password });
  if (!result.success) {
    throw new AuthError(result.error.issues[0]?.message ?? "Invalid input", 400);
  }
  return result.data;
}

function toSafeUser(row: {
  id: string;
  email: string;
  name: string | null;
  lifetime_access: boolean;
}): SafeUser {
  return { id: row.id, email: row.email, name: row.name, lifetimeAccess: row.lifetime_access };
}
