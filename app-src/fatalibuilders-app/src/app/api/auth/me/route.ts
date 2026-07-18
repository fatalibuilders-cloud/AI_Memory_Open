import { NextResponse } from "next/server";
import { getUserBySession } from "@/lib/auth";
import { readSessionCookie } from "@/lib/session-cookie";

export async function GET() {
  const user = await getUserBySession(await readSessionCookie());
  return NextResponse.json({ user });
}
