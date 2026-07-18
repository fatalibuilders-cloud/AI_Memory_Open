import { NextResponse } from "next/server";
import { deleteSession } from "@/lib/auth";
import { clearSessionCookie, readSessionCookie } from "@/lib/session-cookie";

export async function POST() {
  const token = await readSessionCookie();
  if (token) await deleteSession(token);
  await clearSessionCookie();
  return NextResponse.redirect(new URL("/", process.env.APP_URL ?? "http://localhost:3000"), 303);
}
