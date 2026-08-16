import { NextRequest, NextResponse } from "next/server";
import { ApplicationError, submitApplication } from "@/lib/applications";
import { FILE_KINDS, FileError, validateUpload, type FileKind, type StoredFile } from "@/lib/files";
import { parseAmountToCents } from "@/lib/money";

/**
 * Public application intake. Multipart because of the documents; every file is
 * validated by its leading bytes before anything is written.
 */
export async function POST(req: NextRequest) {
  try {
    const form = await req.formData();

    const files: { kind: FileKind; file: StoredFile }[] = [];
    for (const { kind } of FILE_KINDS) {
      for (const entry of form.getAll(`file_${kind}`)) {
        if (!(entry instanceof File) || entry.size === 0) continue;
        const bytes = new Uint8Array(await entry.arrayBuffer());
        files.push({ kind, file: validateUpload(entry.name, bytes) });
      }
    }

    const text = (name: string) => String(form.get(name) ?? "").trim();
    const number = (name: string) => Number(form.get(name) ?? 0);

    const result = await submitApplication(
      {
        masjidName: text("masjidName"),
        city: text("city"),
        country: text("country"),
        locationNote: text("locationNote"),
        congregationNow: number("congregationNow"),
        capacityPlanned: number("capacityPlanned"),
        estimatedCostCents: parseAmountToCents(text("estimatedCost")) ?? 0,
        alreadyRaisedCents: parseAmountToCents(text("alreadyRaised") || "0") ?? 0,
        currency: text("currency") === "KES" ? "KES" : "USD",
        landTitleNumber: text("landTitleNumber"),
        landOwnership: text("landOwnership"),
        titledToTrust: form.get("titledToTrust") === "on",
        trustName: text("trustName"),
        trustRegistration: text("trustRegistration"),
        contactName: text("contactName"),
        contactRole: text("contactRole"),
        contactEmail: text("contactEmail"),
        contactPhone: text("contactPhone"),
        story: text("story"),
        consentTruthful: form.get("consentTruthful") === "on",
        consentPublish: form.get("consentPublish") === "on",
      },
      files,
      { ip: req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ?? null },
    );

    return NextResponse.json(result, { status: 201 });
  } catch (err) {
    if (err instanceof ApplicationError || err instanceof FileError) {
      return NextResponse.json({ error: err.message }, { status: err.status });
    }
    console.error("application submission failed:", err);
    return NextResponse.json(
      { error: "We could not receive that application. Please try again." },
      { status: 500 },
    );
  }
}
