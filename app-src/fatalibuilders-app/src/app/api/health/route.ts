import { NextResponse } from "next/server";

export function GET() {
  return NextResponse.json({
    status: "ok",
    app: "fatalibuilders-app",
    time: new Date().toISOString(),
  });
}
