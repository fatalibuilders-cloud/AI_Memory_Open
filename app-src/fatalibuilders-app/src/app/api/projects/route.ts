import { NextRequest, NextResponse } from "next/server";
import { AuthError, getUserBySession } from "@/lib/auth";
import { readSessionCookie } from "@/lib/session-cookie";
import { createProject, listProjects } from "@/lib/projects";

export async function GET() {
  const user = await getUserBySession(await readSessionCookie());
  if (!user) return NextResponse.json({ error: "Sign in first." }, { status: 401 });
  return NextResponse.json({ projects: await listProjects(user.id) });
}

export async function POST(req: NextRequest) {
  const user = await getUserBySession(await readSessionCookie());
  if (!user) return NextResponse.json({ error: "Sign in first." }, { status: 401 });
  try {
    const body = await req.json().catch(() => ({}));
    const project = await createProject(user.id, body.name ?? "Untitled project");
    return NextResponse.json({ project }, { status: 201 });
  } catch (err) {
    if (err instanceof AuthError) {
      return NextResponse.json({ error: err.message }, { status: err.status });
    }
    console.error("create project failed:", err);
    return NextResponse.json({ error: "Something went wrong. Try again." }, { status: 500 });
  }
}
