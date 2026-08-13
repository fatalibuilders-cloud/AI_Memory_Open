import { NextRequest, NextResponse } from "next/server";
import { getAdminSession } from "@/lib/admin";
import { donationsToCsv, listDonationsForAdmin } from "@/lib/admin-data";

/** Donation export for the accounts. Staff session required. */
export async function GET(req: NextRequest) {
  if (!(await getAdminSession())) {
    return NextResponse.json({ error: "Sign in to continue." }, { status: 401 });
  }

  const status = req.nextUrl.searchParams.get("status") ?? undefined;
  const rows = await listDonationsForAdmin({ status, limit: 10000 });
  const filename = `donations-${new Date().toISOString().slice(0, 10)}.csv`;

  return new NextResponse(donationsToCsv(rows), {
    headers: {
      "Content-Type": "text/csv; charset=utf-8",
      "Content-Disposition": `attachment; filename="${filename}"`,
      "Cache-Control": "no-store",
    },
  });
}
