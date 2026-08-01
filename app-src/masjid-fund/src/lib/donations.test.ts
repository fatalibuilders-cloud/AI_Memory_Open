import { beforeEach, describe, expect, it } from "vitest";
import { resetDbForTests } from "@/db";
import { DonationError } from "./donation";
import { createDonation, getDonationByReference, settleDonation } from "./donations";
import { resetPaymentProviderForTests } from "./payments";
import { getProjectBySlug, getFundStats, listRecentDonations } from "./projects";

const GARISSA = "masjid-al-noor-garissa";
const COMPLETED = "masjid-al-fajr-mombasa";

const base = {
  amountCents: 5000,
  donorEmail: "donor@example.com",
  donorName: "Ali",
};

beforeEach(() => {
  resetDbForTests();
  resetPaymentProviderForTests();
});

describe("createDonation", () => {
  it("records a pending donation and returns a checkout URL", async () => {
    const started = await createDonation({ ...base, projectSlug: GARISSA });
    expect(started.reference).toMatch(/^MF-[0-9A-Z]{8}$/);
    expect(started.checkoutUrl).toContain(started.reference);
    expect(started.liveMode).toBe(false); // built-in simulator

    const donation = await getDonationByReference(started.reference);
    expect(donation?.status).toBe("pending");
    expect(donation?.projectSlug).toBe(GARISSA);
    expect(donation?.amountCents).toBe(5000);
  });

  it("does not count towards the project until it is settled", async () => {
    const before = await getProjectBySlug(GARISSA);
    await createDonation({ ...base, projectSlug: GARISSA });
    const after = await getProjectBySlug(GARISSA);
    expect(after!.raisedCents).toBe(before!.raisedCents);
    expect(after!.donorCount).toBe(before!.donorCount);
  });

  it("keeps zakat out of construction by dropping the project", async () => {
    const started = await createDonation({ ...base, projectSlug: GARISSA, intent: "zakat" });
    const donation = await getDonationByReference(started.reference);
    expect(donation?.intent).toBe("zakat");
    expect(donation?.projectId).toBeNull();
  });

  it("rejects an unknown project with 404 and a finished one with 409", async () => {
    await expect(createDonation({ ...base, projectSlug: "no-such-masjid" })).rejects.toMatchObject({
      status: 404,
    });
    await expect(createDonation({ ...base, projectSlug: COMPLETED })).rejects.toMatchObject({
      status: 409,
    });
  });

  it("rejects invalid input before touching the payment provider", async () => {
    await expect(createDonation({ amountCents: 10, donorEmail: "a@b.com" })).rejects.toBeInstanceOf(
      DonationError,
    );
  });
});

describe("settleDonation", () => {
  it("adds a completed donation to the project total and donor count", async () => {
    const before = await getProjectBySlug(GARISSA);
    const started = await createDonation({ ...base, amountCents: 22000, projectSlug: GARISSA });
    await settleDonation({ reference: started.reference }, "completed");

    const after = await getProjectBySlug(GARISSA);
    expect(after!.raisedCents).toBe(before!.raisedCents + 22000);
    expect(after!.donorCount).toBe(before!.donorCount + 1);
  });

  it("is idempotent — a retried webhook cannot double-count a gift", async () => {
    const started = await createDonation({ ...base, projectSlug: GARISSA });
    const first = await settleDonation({ reference: started.reference }, "completed");
    const second = await settleDonation({ reference: started.reference }, "completed");

    expect(first?.status).toBe("completed");
    expect(second).toBeNull();

    const project = await getProjectBySlug(GARISSA);
    expect(project!.donorCount).toBe(1);
  });

  it("settles by provider reference when the payload carries no donation reference", async () => {
    const started = await createDonation({ ...base, projectSlug: GARISSA });
    const settled = await settleDonation(
      { reference: null, providerRef: `mock_${started.reference}` },
      "completed",
    );
    expect(settled?.reference).toBe(started.reference);
  });

  it("leaves a failed donation out of the totals", async () => {
    const before = await getProjectBySlug(GARISSA);
    const started = await createDonation({ ...base, projectSlug: GARISSA });
    await settleDonation({ reference: started.reference }, "failed");

    const after = await getProjectBySlug(GARISSA);
    expect(after!.raisedCents).toBe(before!.raisedCents);
    expect((await getDonationByReference(started.reference))?.status).toBe("failed");
  });

  it("returns null for a reference that does not exist", async () => {
    expect(await settleDonation({ reference: "MF-NOTHING" }, "completed")).toBeNull();
  });
});

describe("public feeds", () => {
  it("counts settled gifts in the fund total and hides anonymous donors by name", async () => {
    const beforeStats = await getFundStats();

    const named = await createDonation({ ...base, amountCents: 10000, projectSlug: GARISSA });
    await settleDonation({ reference: named.reference }, "completed");
    const hidden = await createDonation({
      ...base,
      amountCents: 7500,
      anonymous: true,
      projectSlug: GARISSA,
    });
    await settleDonation({ reference: hidden.reference }, "completed");

    const stats = await getFundStats();
    expect(stats.raisedCents).toBe(beforeStats.raisedCents + 17500);
    expect(stats.donorCount).toBe(2);

    const recent = await listRecentDonations(10);
    expect(recent).toHaveLength(2);
    expect(recent.map((d) => d.name).sort()).toEqual(["Ali", "Anonymous"]);
  });

  it("omits pending donations from the recent feed", async () => {
    await createDonation({ ...base, projectSlug: GARISSA });
    expect(await listRecentDonations()).toHaveLength(0);
  });
});
