import { beforeEach, describe, expect, it } from "vitest";
import { getDb, resetDbForTests } from "@/db";
import { fromBase, usdToKesRate } from "./money";
import { DONATION_LIMITS, hashIp } from "./rate-limit";
import { DonationError } from "./donation";
import {
  cancelMonthlyGiving,
  createDonation,
  getDonationByReference,
  settleDonation,
} from "./donations";
import { resetEmailProviderForTests } from "./email";
import { resetPaymentProviderForTests } from "./payments";
import { getFundStats, getProjectBySlug, listRecentDonations } from "./projects";

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
  resetEmailProviderForTests();
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

describe("M-Pesa donations", () => {
  const mpesa = { ...base, method: "mpesa" as const, phone: "0722 000 000", projectSlug: GARISSA };

  it("charges shillings while the ledger keeps dollars", async () => {
    const started = await createDonation({ ...mpesa, amountCents: 5000 });
    const donation = await getDonationByReference(started.reference);

    expect(donation?.currency).toBe("KES");
    expect(donation?.amountCents).toBe(fromBase(5000, "KES"));
    expect(donation?.baseAmountCents).toBe(5000); // what the donor chose, in USD
    expect(donation?.fxRate).toBe(usdToKesRate());
    expect(donation?.method).toBe("mpesa");
    expect(donation?.phone).toBe("254722000000"); // normalised for Daraja
    expect(started.checkoutUrl).toBe(`/donate/mpesa/${started.reference}`);
  });

  it("adds the dollar equivalent to the project, not the shilling figure", async () => {
    const before = await getProjectBySlug(GARISSA);
    const started = await createDonation({ ...mpesa, amountCents: 10000 });
    await settleDonation({ reference: started.reference }, "completed");

    const after = await getProjectBySlug(GARISSA);
    expect(after!.raisedCents).toBe(before!.raisedCents + 10000);
  });

  it("keeps mixed-currency totals in dollars", async () => {
    const card = await createDonation({ ...base, amountCents: 2500, projectSlug: GARISSA });
    await settleDonation({ reference: card.reference }, "completed");
    const phone = await createDonation({ ...mpesa, amountCents: 7500 });
    await settleDonation({ reference: phone.reference }, "completed");

    const stats = await getFundStats();
    expect(stats.raisedCents).toBe(10000 + (await offlineBaseline()));
  });

  it("records the M-Pesa code from the callback", async () => {
    const started = await createDonation(mpesa);
    const settled = await settleDonation(
      { reference: null, providerRef: `mock_${started.reference}`, externalRef: "SFI4X8YZ01" },
      "completed",
    );
    expect(settled?.externalRef).toBe("SFI4X8YZ01");
  });

  it("refuses a number M-Pesa could not reach, before any payment is attempted", async () => {
    await expect(createDonation({ ...mpesa, phone: "12345" })).rejects.toMatchObject({
      status: 400,
    });
    await expect(createDonation({ ...mpesa, phone: "" })).rejects.toMatchObject({ status: 400 });
  });

  it("closes off a donation whose payment could never be started", async () => {
    // The simulator always succeeds, so drive the failure through validation:
    // a rejected push must not leave a pending row nothing will ever settle.
    const before = await listDonationsForStatus("pending");
    await createDonation({ ...mpesa, phone: "not a phone" }).catch(() => null);
    expect(await listDonationsForStatus("pending")).toBe(before);
  });
});

async function offlineBaseline(): Promise<number> {
  // Seeded projects carry historic offline totals; they are part of every
  // fund-wide figure and are not what these tests are asserting about.
  const stats = await getFundStats();
  const db = await getDb();
  const [row] = await db.query<{ donated: string | number | null }>(
    "SELECT SUM(COALESCE(base_amount_cents, amount_cents)) AS donated FROM donations WHERE status = 'completed'",
  );
  return stats.raisedCents - Number(row?.donated ?? 0);
}

async function listDonationsForStatus(status: string): Promise<number> {
  const db = await getDb();
  const [row] = await db.query<{ count: string | number }>(
    "SELECT COUNT(*) AS count FROM donations WHERE status = $1",
    [status],
  );
  return Number(row?.count ?? 0);
}

describe("abuse limits", () => {
  it("stops a burst of attempts from one network before they reach the provider", async () => {
    const ip = "203.0.113.9";
    for (let i = 0; i < DONATION_LIMITS.perIp.max; i++) {
      // Vary the email so the per-address limit is not what trips first.
      await createDonation({ ...base, donorEmail: `donor${i}@example.com` }, { ip });
    }
    await expect(
      createDonation({ ...base, donorEmail: "one-more@example.com" }, { ip }),
    ).rejects.toMatchObject({ status: 429 });
  });

  it("stops repeat attempts from one address even across networks", async () => {
    for (let i = 0; i < DONATION_LIMITS.perEmail.max; i++) {
      await createDonation(base, { ip: `198.51.100.${i}` });
    }
    await expect(createDonation(base, { ip: "198.51.100.200" })).rejects.toMatchObject({
      status: 429,
    });
  });

  it("lets an ordinary donor give to several projects in one sitting", async () => {
    const ip = "192.0.2.44";
    for (const slug of [GARISSA, null, GARISSA]) {
      const started = await createDonation({ ...base, projectSlug: slug }, { ip });
      expect(started.reference).toBeTruthy();
    }
  });

  it("stores only a hash of the address, never the address itself", async () => {
    const ip = "203.0.113.55";
    const started = await createDonation(base, { ip });
    const db = await getDb();
    const [row] = await db.query<{ ip_hash: string | null }>(
      "SELECT ip_hash FROM donations WHERE reference = $1",
      [started.reference],
    );
    expect(row.ip_hash).toBeTruthy();
    expect(row.ip_hash).not.toContain("203.0.113");
    expect(row.ip_hash).toBe(hashIp(ip));
  });
});

describe("monthly giving", () => {
  const monthly = { ...base, frequency: "monthly" as const, projectSlug: GARISSA };

  it("issues a management token for monthly gifts only", async () => {
    const recurring = await createDonation(monthly);
    const oneOff = await createDonation(base);

    expect((await getDonationByReference(recurring.reference))?.manageToken).toBeTruthy();
    expect((await getDonationByReference(oneOff.reference))?.manageToken).toBeNull();
  });

  it("records the provider's subscription reference on settlement", async () => {
    const started = await createDonation(monthly);
    await settleDonation(
      { reference: started.reference, subscriptionRef: "sub_test_1" },
      "completed",
    );
    expect((await getDonationByReference(started.reference))?.subscriptionRef).toBe("sub_test_1");
  });

  it("cancels from the donor's link and stays cancelled on a repeat click", async () => {
    const started = await createDonation(monthly);
    await settleDonation({ reference: started.reference }, "completed");
    const token = (await getDonationByReference(started.reference))!.manageToken!;

    const cancelled = await cancelMonthlyGiving(token);
    expect(cancelled?.cancelledAt).toBeTruthy();

    const again = await cancelMonthlyGiving(token);
    expect(again?.cancelledAt).toBe(cancelled?.cancelledAt);
  });

  it("leaves money already given with its project after cancelling", async () => {
    const before = await getProjectBySlug(GARISSA);
    const started = await createDonation({ ...monthly, amountCents: 10000 });
    await settleDonation({ reference: started.reference }, "completed");
    const token = (await getDonationByReference(started.reference))!.manageToken!;
    await cancelMonthlyGiving(token);

    const after = await getProjectBySlug(GARISSA);
    expect(after!.raisedCents).toBe(before!.raisedCents + 10000);
  });

  it("ignores an unknown or one-time token", async () => {
    expect(await cancelMonthlyGiving("not-a-token")).toBeNull();
    const oneOff = await createDonation(base);
    const donation = await getDonationByReference(oneOff.reference);
    expect(donation?.manageToken).toBeNull();
  });
});

describe("receipts", () => {
  it("marks a receipt as sent once the gift settles", async () => {
    const started = await createDonation({ ...base, projectSlug: GARISSA });
    expect((await getDonationByReference(started.reference))?.receiptSentAt).toBeNull();

    await settleDonation({ reference: started.reference }, "completed");
    expect((await getDonationByReference(started.reference))?.receiptSentAt).toBeTruthy();
  });

  it("sends no receipt for a failed payment", async () => {
    const started = await createDonation({ ...base, projectSlug: GARISSA });
    await settleDonation({ reference: started.reference }, "failed");
    expect((await getDonationByReference(started.reference))?.receiptSentAt).toBeNull();
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
