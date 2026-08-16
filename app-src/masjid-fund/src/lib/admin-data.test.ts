import { beforeEach, describe, expect, it } from "vitest";
import { resetDbForTests } from "@/db";
import { hashPassword, verifyPassword } from "./admin";
import {
  addProjectCost,
  createProject,
  donationsToCsv,
  getAdminStats,
  listDonationsForAdmin,
  parseOrThrow,
  postProjectUpdate,
  projectSchema,
  updateProject,
} from "./admin-data";
import { createDonation, recordOfflineDonation, settleDonation } from "./donations";
import { resetEmailProviderForTests } from "./email";
import { resetPaymentProviderForTests } from "./payments";
import { getProjectBySlug, listProjects } from "./projects";

const project = {
  slug: "masjid-al-amin-lamu",
  name: "Masjid al-Amin",
  city: "Lamu",
  country: "Kenya",
  summary: "A 200-capacity masjid for the fishing community on the north shore.",
  story: "The current prayer room floods at spring tide and holds barely forty people.",
  status: "planning" as const,
  goalCents: 4500000,
  offlineRaisedCents: 250000,
  capacity: 200,
  accent: "teal" as const,
  position: 9,
};

beforeEach(() => {
  resetDbForTests();
  resetPaymentProviderForTests();
  resetEmailProviderForTests();
});

describe("password hashing", () => {
  it("verifies a correct password and rejects a wrong one", async () => {
    const stored = await hashPassword("correct horse battery staple");
    expect(await verifyPassword("correct horse battery staple", stored)).toBe(true);
    expect(await verifyPassword("wrong password", stored)).toBe(false);
  });

  it("rejects a malformed stored value instead of throwing", async () => {
    expect(await verifyPassword("anything", "not-a-hash")).toBe(false);
    expect(await verifyPassword("anything", "")).toBe(false);
  });

  it("salts, so the same password hashes differently each time", async () => {
    expect(await hashPassword("same")).not.toBe(await hashPassword("same"));
  });
});

describe("project validation", () => {
  it("rejects a slug that would break the URL", () => {
    expect(() => parseOrThrow(projectSchema, { ...project, slug: "Not A Slug" })).toThrow();
  });

  it("rejects a budget of zero", () => {
    expect(() => parseOrThrow(projectSchema, { ...project, goalCents: 0 })).toThrow();
  });
});

describe("managing projects", () => {
  it("creates a project that appears on the public list", async () => {
    await createProject(project);
    const created = await getProjectBySlug(project.slug);
    expect(created?.name).toBe("Masjid al-Amin");
    expect(created?.raisedCents).toBe(250000); // offline total counts immediately
    expect((await listProjects()).some((p) => p.slug === project.slug)).toBe(true);
  });

  it("refuses a duplicate slug", async () => {
    await createProject(project);
    await expect(createProject(project)).rejects.toMatchObject({ status: 409 });
  });

  it("keeps the offline total and sort order when edited", async () => {
    await createProject(project);
    await updateProject(project.slug, { ...project, name: "Masjid al-Amin (phase 2)" });

    const edited = await getProjectBySlug(project.slug);
    expect(edited?.name).toBe("Masjid al-Amin (phase 2)");
    expect(edited?.offlineRaisedCents).toBe(250000);
    expect(edited?.position).toBe(9);
  });

  it("follows a slug change so the project is still reachable", async () => {
    await createProject(project);
    await updateProject(project.slug, { ...project, slug: "masjid-al-amin-lamu-2" });

    expect(await getProjectBySlug(project.slug)).toBeNull();
    expect((await getProjectBySlug("masjid-al-amin-lamu-2"))?.name).toBe("Masjid al-Amin");
  });

  it("adds costed items and build updates to the public page", async () => {
    await createProject(project);
    await addProjectCost(project.slug, {
      label: "A roofing sheet",
      detail: "One of the 60 sheets over the hall.",
      unitCostCents: 2800,
      position: 1,
    });
    await postProjectUpdate(project.slug, {
      title: "Foundations poured",
      body: "The slab was cast on Tuesday and is curing.",
    });

    const detail = await getProjectBySlug(project.slug);
    expect(detail?.costs).toHaveLength(1);
    expect(detail?.costs[0].unitCostCents).toBe(2800);
    expect(detail?.updates[0].title).toBe("Foundations poured");
  });

  it("rejects edits to a project that no longer exists", async () => {
    await expect(updateProject("ghost-masjid", project)).rejects.toMatchObject({ status: 404 });
  });
});

describe("offline gifts", () => {
  it("counts towards the project the moment it is recorded", async () => {
    await createProject(project);
    const before = await getProjectBySlug(project.slug);

    const donation = await recordOfflineDonation({
      amountCents: 75000,
      projectSlug: project.slug,
      donorName: "Community collection",
      donorEmail: null,
      intent: "sadaqah_jariyah",
      note: "Bank transfer ref 88213",
      anonymous: false,
    });

    expect(donation.status).toBe("completed");
    const after = await getProjectBySlug(project.slug);
    expect(after!.raisedCents).toBe(before!.raisedCents + 75000);
  });

  it("rejects an unknown project", async () => {
    await expect(
      recordOfflineDonation({
        amountCents: 1000,
        projectSlug: "no-such-masjid",
        donorName: null,
        donorEmail: null,
        intent: "sadaqah_jariyah",
        note: null,
        anonymous: false,
      }),
    ).rejects.toMatchObject({ status: 404 });
  });
});

describe("admin donation views", () => {
  it("filters by status and summarises the ledger", async () => {
    const settled = await createDonation({
      amountCents: 5000,
      donorEmail: "a@example.com",
      projectSlug: "masjid-al-noor-garissa",
    });
    await settleDonation({ reference: settled.reference }, "completed");
    await createDonation({ amountCents: 9000, donorEmail: "b@example.com" });

    expect(await listDonationsForAdmin({ status: "completed" })).toHaveLength(1);
    expect(await listDonationsForAdmin({ status: "pending" })).toHaveLength(1);
    expect(await listDonationsForAdmin({})).toHaveLength(2);

    const stats = await getAdminStats();
    expect(stats.completedCount).toBe(1);
    expect(stats.pendingCount).toBe(1);
    expect(stats.settledCents).toBe(5000);
  });
});

describe("donationsToCsv", () => {
  const row = {
    reference: "MF-1",
    createdAt: "2026-08-01T10:00:00.000Z",
    completedAt: null,
    amountCents: 12550,
    currency: "USD",
    status: "completed",
    frequency: "one_time",
    intent: "sadaqah_jariyah",
    provider: "stripe",
    donorName: 'Ali "the builder"',
    donorEmail: "ali@example.com",
    anonymous: false,
    dedication: null,
    projectName: "Masjid al-Noor",
    cancelledAt: null,
    receiptSentAt: null,
    manageToken: null,
  };

  it("writes a header and formats money in whole units", () => {
    const csv = donationsToCsv([row]);
    expect(csv.split("\n")[0]).toContain("reference,created_at");
    expect(csv).toContain('"125.50"');
  });

  it("escapes quotes and neutralises formula injection", () => {
    const csv = donationsToCsv([{ ...row, donorName: "=cmd|'/c calc'!A1" }]);
    expect(csv).toContain(`"'=cmd|'/c calc'!A1"`);
    expect(donationsToCsv([row])).toContain('"Ali ""the builder"""');
  });
});
