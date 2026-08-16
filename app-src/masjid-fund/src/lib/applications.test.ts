import { beforeEach, describe, expect, it } from "vitest";
import { resetDbForTests } from "@/db";
import {
  ApplicationError,
  getApplicationById,
  getApplicationByToken,
  getDocumentBytes,
  linkApplicationToProject,
  listApplicationEvents,
  listApplications,
  setApplicationStatus,
  submitApplication,
} from "./applications";
import { createProject } from "./admin-data";
import { resetEmailProviderForTests } from "./email";
import { FileError, validateUpload } from "./files";
import { getProjectBySlug } from "./projects";

const PDF = new Uint8Array([0x25, 0x50, 0x44, 0x46, 0x2d, 0x31, 0x2e, 0x37, 0x0a, 0x20]);
const PNG = new Uint8Array([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 0x00]);

const input = {
  masjidName: "Masjid al-Amin",
  city: "Lamu",
  country: "Kenya",
  locationNote: "North shore, beside the fish market",
  congregationNow: 120,
  capacityPlanned: 200,
  estimatedCostCents: 4500000,
  alreadyRaisedCents: 250000,
  currency: "USD" as const,
  landTitleNumber: "LAMU/BLOCK II/455",
  landOwnership: "waqf_trust" as const,
  titledToTrust: true,
  trustName: "Lamu Muslim Waqf Trust",
  trustRegistration: "OP.218/051",
  contactName: "Ali Ahmed",
  contactRole: "Chairman",
  contactEmail: "ali@example.com",
  contactPhone: "+254700000000",
  story:
    "The community prays in a rented room that floods at spring tide and holds barely forty people. The land was donated by the village elders and titled to the waqf trust in 2024.",
  consentTruthful: true,
  consentPublish: true,
};

const requiredFiles = [
  { kind: "title_deed" as const, file: validateUpload("deed.pdf", PDF) },
  { kind: "drawings" as const, file: validateUpload("plans.pdf", PDF) },
  { kind: "boq" as const, file: validateUpload("boq.pdf", PDF) },
];

beforeEach(() => {
  resetDbForTests();
  resetEmailProviderForTests();
});

describe("upload validation", () => {
  it("accepts PDF, JPG and PNG by their leading bytes", () => {
    expect(validateUpload("deed.pdf", PDF).contentType).toBe("application/pdf");
    expect(validateUpload("site.png", PNG).contentType).toBe("image/png");
  });

  it("rejects a file whose bytes are not one of the accepted formats", () => {
    const script = new TextEncoder().encode("<?php system($_GET['c']); ?>");
    expect(() => validateUpload("deed.pdf", script)).toThrow(FileError);
  });

  it("rejects an empty file and one over the size cap", () => {
    expect(() => validateUpload("empty.pdf", new Uint8Array())).toThrow(FileError);
    const huge = new Uint8Array(5 * 1024 * 1024);
    huge.set(PDF.slice(0, 4));
    expect(() => validateUpload("big.pdf", huge)).toThrow(FileError);
  });

  it("strips paths and odd characters from the stored filename", () => {
    expect(validateUpload("../../etc/pass<wd>.pdf", PDF).filename).toBe("passwd.pdf");
    expect(validateUpload("deed.exe", PDF).filename).toBe("deed.pdf"); // extension follows the bytes
  });
});

describe("submitApplication", () => {
  it("stores the application, its documents and a submitted event", async () => {
    const { reference, statusToken } = await submitApplication(input, requiredFiles);
    expect(reference).toMatch(/^MA-[A-Z0-9]{8}$/);

    const application = await getApplicationByToken(statusToken);
    expect(application?.masjidName).toBe("Masjid al-Amin");
    expect(application?.status).toBe("submitted");
    expect(application?.documents).toHaveLength(3);
    expect(application?.documents.map((d) => d.kind).sort()).toEqual([
      "boq",
      "drawings",
      "title_deed",
    ]);

    const events = await listApplicationEvents(application!.id);
    expect(events).toHaveLength(1);
    expect(events[0]).toMatchObject({ actor: "applicant", action: "submitted" });
  });

  it("round-trips document bytes unchanged", async () => {
    const { statusToken } = await submitApplication(input, requiredFiles);
    const application = await getApplicationByToken(statusToken);
    const stored = await getDocumentBytes(application!.documents[0].id);
    expect(Array.from(stored!.bytes)).toEqual(Array.from(PDF));
    expect(stored!.contentType).toBe("application/pdf");
  });

  it("refuses a submission missing the title deed, drawings or BoQ", async () => {
    await expect(
      submitApplication(input, requiredFiles.filter((f) => f.kind !== "boq")),
    ).rejects.toBeInstanceOf(FileError);
  });

  it("rejects incomplete or unconsented applications", async () => {
    await expect(
      submitApplication({ ...input, contactEmail: "not-an-email" }, requiredFiles),
    ).rejects.toMatchObject({ status: 400 });
    await expect(
      submitApplication({ ...input, consentPublish: false }, requiredFiles),
    ).rejects.toBeInstanceOf(ApplicationError);
    await expect(
      submitApplication({ ...input, story: "Needs money." }, requiredFiles),
    ).rejects.toBeInstanceOf(ApplicationError);
  });

  it("throttles repeat submissions from the same address", async () => {
    for (let i = 0; i < 3; i++) await submitApplication(input, requiredFiles);
    await expect(submitApplication(input, requiredFiles)).rejects.toMatchObject({ status: 429 });
  });

  it("keeps applications out of the public project list", async () => {
    await submitApplication(input, requiredFiles);
    expect(await getProjectBySlug("masjid-al-amin-lamu")).toBeNull();
  });
});

describe("review workflow", () => {
  async function submitted() {
    const { statusToken } = await submitApplication(input, requiredFiles);
    return (await getApplicationByToken(statusToken))!;
  }

  it("moves through review and records who did what", async () => {
    const application = await submitted();
    await setApplicationStatus(application.id, "in_review", null, "staff@example.com");
    const updated = await setApplicationStatus(
      application.id,
      "needs_info",
      "We still need the priced bill of quantities.",
      "staff@example.com",
    );

    expect(updated?.status).toBe("needs_info");
    expect(updated?.statusNote).toContain("bill of quantities");

    const events = await listApplicationEvents(application.id);
    expect(events.map((e) => e.action)).toEqual(["submitted", "in_review", "needs_info"]);
    expect(events[2].actor).toBe("staff@example.com");
  });

  it("records a decision date when declined", async () => {
    const application = await submitted();
    const declined = await setApplicationStatus(
      application.id,
      "rejected",
      "The title is held by an individual and cannot be transferred.",
      "staff@example.com",
    );
    expect(declined?.decidedAt).toBeTruthy();
  });

  it("refuses to approve before a project exists", async () => {
    const application = await submitted();
    await expect(
      setApplicationStatus(application.id, "approved", null, "staff@example.com"),
    ).rejects.toMatchObject({ status: 409 });
  });

  it("approves once linked to a published project", async () => {
    const application = await submitted();
    await createProject({
      slug: "masjid-al-amin-lamu",
      name: "Masjid al-Amin",
      city: "Lamu",
      country: "Kenya",
      summary: "A 200-capacity masjid for the fishing community on the north shore.",
      story: input.story,
      status: "planning",
      goalCents: 4500000,
      offlineRaisedCents: 250000,
      capacity: 200,
      accent: "teal",
      position: 1,
    });
    const project = await getProjectBySlug("masjid-al-amin-lamu");
    await linkApplicationToProject(application.id, project!.id, "staff@example.com");

    const approved = await setApplicationStatus(
      application.id,
      "approved",
      "Approved after the site visit.",
      "staff@example.com",
    );
    expect(approved?.status).toBe("approved");
    expect(approved?.projectSlug).toBe("masjid-al-amin-lamu");

    const events = await listApplicationEvents(application.id);
    expect(events.map((e) => e.action)).toContain("published");
  });

  it("filters the staff list by status", async () => {
    const first = await submitted();
    await submitApplication({ ...input, contactEmail: "other@example.com" }, requiredFiles);
    await setApplicationStatus(first.id, "in_review", null, "staff@example.com");

    expect(await listApplications("submitted")).toHaveLength(1);
    expect(await listApplications("in_review")).toHaveLength(1);
    expect(await listApplications()).toHaveLength(2);
  });

  it("reports an unknown application rather than failing silently", async () => {
    await expect(
      setApplicationStatus(
        "11111111-1111-4111-8111-111111111111",
        "in_review",
        null,
        "staff@example.com",
      ),
    ).rejects.toMatchObject({ status: 404 });
    expect(await getApplicationById("11111111-1111-4111-8111-111111111111")).toBeNull();
    expect(await getApplicationByToken("not-a-token")).toBeNull();
  });
});
