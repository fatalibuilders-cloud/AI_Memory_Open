import { NextResponse } from "next/server";
import { getFundStats } from "@/lib/projects";

export const dynamic = "force-dynamic";

export async function GET() {
  const stats = await getFundStats();
  return NextResponse.json(stats);
}
