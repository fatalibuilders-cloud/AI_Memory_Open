import { NextRequest, NextResponse } from "next/server";
import { AuthError, getUserBySession } from "@/lib/auth";
import { readSessionCookie } from "@/lib/session-cookie";
import { getProject, updateProject } from "@/lib/projects";

type Params = { params: Promise<{ id: string }> };

export async function GET(_req: NextRequest, { params }: Params) {
  const user = await getUserBySession(await readSessionCookie());
  if (!user) return NextResponse.json({ error: "Sign in first." }, { status: 401 });
  try {
    const { id } = await params;
    return NextResponse.json({ project: await getProject(user.id, id) });
  } catch (err) {
    return handle(err);
  }
}

export async function PUT(req: NextRequest, { params }: Params) {
  const user = await getUserBySession(await readSessionCookie());
  if (!user) return NextResponse.json({ error: "Sign in first." }, { status: 401 });
  try {
    const { id } = await params;
    const body = await req.json().catch(() => ({}));
    const project = await updateProject(user.id, id, {
      name: body.name,
      data: body.data,
      status: body.status,
    });
    return NextResponse.json({ project });
  } catch (err) {
    return handle(err);
  }
}

function handle(err: unknown) {
  if (err instanceof AuthError) {
    return NextResponse.json({ error: err.message }, { status: err.status });
  }
  console.error("project route failed:", err);
  return NextResponse.json({ error: "Something went wrong. Try again." }, { status: 500 });
}
