import { NextResponse } from "next/server";
import { getDb } from "@/db";

export async function GET() {
  try {
    const db = await getDb();
    await db.query("SELECT 1");
    return NextResponse.json({ status: "ok" });
  } catch (err) {
    console.error("health check failed:", err);
    return NextResponse.json({ status: "degraded" }, { status: 503 });
  }
}
