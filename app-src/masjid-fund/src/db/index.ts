import { BOOTSTRAP_SQL, SEED_SQL } from "./schema";

/**
 * Database access with driver selection:
 * - DATABASE_URL set   → managed PostgreSQL (production)
 * - DATABASE_URL unset → embedded PGlite: in-memory under test, on-disk at
 *   .pglite/ for local development. Same Postgres dialect everywhere.
 *
 * Sample projects are seeded unless SKIP_SEED=1, so a fresh checkout has
 * something to browse. The seed is idempotent.
 */

// Minimal query surface shared by both drivers.
export interface Db {
  query<R = Record<string, unknown>>(sql: string, params?: unknown[]): Promise<R[]>;
}

let dbPromise: Promise<Db> | null = null;

export function getDb(): Promise<Db> {
  if (!dbPromise) dbPromise = init();
  return dbPromise;
}

/** Test-only: drop the singleton so each test file gets a fresh in-memory DB. */
export function resetDbForTests(): void {
  dbPromise = null;
}

async function init(): Promise<Db> {
  const url = process.env.DATABASE_URL;
  if (url) {
    const { Pool } = await import("pg");
    const pool = new Pool({ connectionString: url });
    await pool.query(BOOTSTRAP_SQL);
    if (process.env.SKIP_SEED !== "1") await pool.query(SEED_SQL);
    return {
      async query(sql, params) {
        const res = await pool.query(sql, params as unknown[]);
        return res.rows;
      },
    };
  }

  // A production deployment with no DATABASE_URL would run on a disposable
  // database — donations recorded there vanish with the container. That is fine
  // for a shared test deployment, but only when it is asked for explicitly.
  const ephemeral = process.env.ALLOW_EPHEMERAL_DB === "1";
  if (process.env.NODE_ENV === "production" && !ephemeral) {
    throw new Error(
      "DATABASE_URL is not set. Point it at a managed PostgreSQL instance, or set " +
        "ALLOW_EPHEMERAL_DB=1 to run a throwaway test deployment whose donations are lost on restart.",
    );
  }
  if (ephemeral) {
    console.warn(
      "[db] Running on an in-memory database — every donation is lost when this instance restarts.",
    );
  }

  const { PGlite } = await import("@electric-sql/pglite");
  const target =
    process.env.NODE_ENV === "test" || ephemeral ? "memory://" : ".pglite";
  const pglite = new PGlite(target);
  await pglite.exec(BOOTSTRAP_SQL);
  if (process.env.SKIP_SEED !== "1") await pglite.exec(SEED_SQL);
  return {
    async query(sql, params) {
      const res = await pglite.query(sql, params as unknown[]);
      return res.rows as never[];
    },
  };
}
