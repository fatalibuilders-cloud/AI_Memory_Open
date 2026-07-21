import { beforeEach, describe, expect, it } from "vitest";
import { resetDbForTests } from "@/db";
import {
  AuthError,
  createSession,
  deleteSession,
  getUserBySession,
  login,
  signup,
} from "./auth";

beforeEach(() => {
  resetDbForTests();
});

describe("signup", () => {
  it("creates a user and returns safe fields only", async () => {
    const user = await signup("Ali@Example.com", "password123");
    expect(user.email).toBe("ali@example.com"); // normalized
    expect(user.lifetimeAccess).toBe(false);
    expect(user).not.toHaveProperty("passwordHash");
  });

  it("rejects duplicate emails with 409", async () => {
    await signup("dup@example.com", "password123");
    await expect(signup("dup@example.com", "password456")).rejects.toMatchObject({
      status: 409,
    });
  });

  it("rejects invalid email and short password with 400", async () => {
    await expect(signup("not-an-email", "password123")).rejects.toMatchObject({ status: 400 });
    await expect(signup("ok@example.com", "short")).rejects.toMatchObject({ status: 400 });
  });
});

describe("login", () => {
  it("logs in with correct credentials", async () => {
    await signup("builder@example.com", "password123");
    const user = await login("builder@example.com", "password123");
    expect(user.email).toBe("builder@example.com");
  });

  it("rejects wrong password and unknown email with 401", async () => {
    await signup("known@example.com", "password123");
    await expect(login("known@example.com", "wrongpass99")).rejects.toMatchObject({ status: 401 });
    await expect(login("unknown@example.com", "password123")).rejects.toMatchObject({
      status: 401,
    });
  });

  it("throws AuthError instances", async () => {
    await expect(login("nobody@example.com", "password123")).rejects.toBeInstanceOf(AuthError);
  });
});

describe("sessions", () => {
  it("round-trips: create → resolve user → delete → gone", async () => {
    const user = await signup("session@example.com", "password123");
    const { token, expiresAt } = await createSession(user.id);
    expect(expiresAt.getTime()).toBeGreaterThan(Date.now());

    const resolved = await getUserBySession(token);
    expect(resolved?.email).toBe("session@example.com");

    await deleteSession(token);
    expect(await getUserBySession(token)).toBeNull();
  });

  it("returns null for missing or bogus tokens", async () => {
    expect(await getUserBySession(undefined)).toBeNull();
    expect(await getUserBySession("bogus-token")).toBeNull();
  });
});
