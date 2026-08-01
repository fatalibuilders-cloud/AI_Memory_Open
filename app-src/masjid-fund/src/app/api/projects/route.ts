import { NextResponse } from "next/server";
import { listProjects } from "@/lib/projects";

export const dynamic = "force-dynamic";

export async function GET() {
  const projects = await listProjects();
  return NextResponse.json({ projects });
}
