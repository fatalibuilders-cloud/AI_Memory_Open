import { describe, expect, it } from "vitest";
import type { Donation } from "@/lib/donations";
import { getOrg, receiptNotice } from "@/lib/org";
import { cancellationEmail, receiptEmail } from "./templates";

const donation: Donation = {
  reference: "MF-7K2QX9T4",
  projectId: "p1",
  projectName: "Masjid al-Noor",
  projectSlug: "masjid-al-noor-garissa",
  amountCents: 22000,
  currency: "USD",
  baseAmountCents: 22000,
  fxRate: 1,
  method: "card",
  phone: null,
  externalRef: null,
  frequency: "monthly",
  intent: "sadaqah_jariyah",
  donorName: "Ali",
  donorEmail: "ali@example.com",
  anonymous: false,
  dedication: "On behalf of my father",
  message: null,
  status: "completed",
  createdAt: "2026-08-01T10:00:00.000Z",
  completedAt: "2026-08-01T10:00:05.000Z",
  manageToken: "tok_123",
  subscriptionRef: "sub_1",
  cancelledAt: null,
  receiptSentAt: null,
};

describe("receiptEmail", () => {
  const org = getOrg();
  const message = receiptEmail(donation, org, {
    manageUrl: "https://example.org/giving/tok_123",
    projectUrl: "https://example.org/projects/masjid-al-noor-garissa",
  });

  it("addresses the donor and carries the reference in the subject", () => {
    expect(message.to).toBe("ali@example.com");
    expect(message.subject).toContain("MF-7K2QX9T4");
    expect(message.subject).toContain("$220 each month");
    expect(message.text).toContain("Assalamu alaikum Ali,");
  });

  it("states the amount, project and dedication in both formats", () => {
    for (const body of [message.html, message.text]) {
      expect(body).toContain("$220 each month");
      expect(body).toContain("Masjid al-Noor");
      expect(body).toContain("On behalf of my father");
    }
  });

  it("includes the management link for a monthly gift", () => {
    expect(message.html).toContain("https://example.org/giving/tok_123");
    expect(message.text).toContain("https://example.org/giving/tok_123");
  });

  it("leaves the management link out of a one-time receipt", () => {
    const oneOff = receiptEmail({ ...donation, frequency: "one_time" }, org, {
      manageUrl: null,
      projectUrl: null,
    });
    expect(oneOff.html).not.toContain("/giving/");
    expect(oneOff.subject).toBe("Your donation MF-7K2QX9T4 — $220");
  });

  it("escapes donor-supplied text so a name cannot inject markup", () => {
    const nasty = receiptEmail(
      { ...donation, donorName: '<script>alert("x")</script>' },
      org,
      { manageUrl: null, projectUrl: null },
    );
    expect(nasty.html).not.toContain("<script>");
    expect(nasty.html).toContain("&lt;script&gt;");
  });

  it("does not claim a tax status the organisation does not have", () => {
    expect(receiptNotice(org)).toContain("no registration number configured");
    const registered = receiptNotice({ ...org, registration: "OP.218/051", registered: true });
    expect(registered).toContain("OP.218/051");
    expect(registered).toContain("not a tax-deduction receipt");
  });
});

describe("cancellationEmail", () => {
  it("confirms the cancellation and reassures about past gifts", () => {
    const message = cancellationEmail({ ...donation, cancelledAt: "2026-08-02T00:00:00.000Z" }, getOrg());
    expect(message.subject).toContain("Monthly giving cancelled");
    expect(message.text).toContain("Nothing further will be charged");
    expect(message.text).toContain("stay with the project");
  });
});
