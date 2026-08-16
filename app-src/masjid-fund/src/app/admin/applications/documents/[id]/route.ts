import { NextResponse } from "next/server";
import { getAdminSession } from "@/lib/admin";
import { getDocumentBytes } from "@/lib/applications";

/**
 * Staff-only document download.
 *
 * Served as an attachment with sniffing disabled, so an uploaded file is never
 * rendered in the context of this origin. Applicant uploads are untrusted
 * input, and this is the only route that ever hands them back.
 */
export async function GET(
  _req: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  if (!(await getAdminSession())) {
    return NextResponse.json({ error: "Sign in to continue." }, { status: 401 });
  }

  const { id } = await params;
  const document = await getDocumentBytes(id);
  if (!document) {
    return NextResponse.json({ error: "Not found." }, { status: 404 });
  }

  return new NextResponse(Buffer.from(document.bytes), {
    headers: {
      "Content-Type": document.contentType,
      "Content-Disposition": `attachment; filename="${document.filename}"`,
      "X-Content-Type-Options": "nosniff",
      "Content-Security-Policy": "default-src 'none'; sandbox",
      "Cache-Control": "private, no-store",
    },
  });
}
