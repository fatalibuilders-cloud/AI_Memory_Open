import { NextRequest, NextResponse } from "next/server";
import { AuthError, createSession, login } from "@/lib/auth";
import { setSessionCookie } from "@/lib/session-cookie";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json().catch(() => ({}));
    const user = await login(body.email ?? "", body.password ?? "");
    const { token, expiresAt } = await createSession(user.id);
    await setSessionCookie(token, expiresAt);
    return NextResponse.json({ user });
  } catch (err) {
    if (err instanceof AuthError) {
      return NextResponse.json({ error: err.message }, { status: err.status });
    }
    console.error("login failed:", err);
    return NextResponse.json({ error: "Something went wrong. Try again." }, { status: 500 });
  }
}
