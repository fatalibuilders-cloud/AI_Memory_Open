import { NextRequest, NextResponse } from "next/server";
import { AuthError, getUserBySession } from "@/lib/auth";
import { readSessionCookie } from "@/lib/session-cookie";
import { getProject } from "@/lib/projects";
import { projectDataSchema } from "@/lib/project-schema";
import { buildProjectPdf } from "@/lib/export-pdf";

type Params = { params: Promise<{ id: string }> };

export async function GET(_req: NextRequest, { params }: Params) {
  const user = await getUserBySession(await readSessionCookie());
  if (!user) return NextResponse.json({ error: "Sign in first." }, { status: 401 });
  if (!user.lifetimeAccess) {
    return NextResponse.json(
      { error: "PDF export is a paid feature. Get lifetime access for $30." },
      { status: 402 },
    );
  }

  try {
    const { id } = await params;
    const project = await getProject(user.id, id);
    const parsed = projectDataSchema.safeParse(project.data);
    if (!parsed.success) {
      return NextResponse.json(
        { error: "Complete the project details before exporting." },
        { status: 400 },
      );
    }
    const pdf = await buildProjectPdf(project.name, parsed.data);
    const safeName = project.name.replace(/[^\w\- ]+/g, "").trim() || "project";
    return new NextResponse(new Uint8Array(pdf), {
      status: 200,
      headers: {
        "Content-Type": "application/pdf",
        "Content-Disposition": `attachment; filename="${safeName} - Fatalibuilders.pdf"`,
      },
    });
  } catch (err) {
    if (err instanceof AuthError) {
      return NextResponse.json({ error: err.message }, { status: err.status });
    }
    console.error("pdf export failed:", err);
    return NextResponse.json({ error: "Export failed. Try again." }, { status: 500 });
  }
}
