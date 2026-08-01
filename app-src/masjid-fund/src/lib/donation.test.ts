import { describe, expect, it } from "vitest";
import { DonationError, displayDonorName, parseDonationInput } from "./donation";
import { MAX_DONATION_CENTS } from "./money";

const valid = {
  amountCents: 5000,
  donorEmail: "Donor@Example.com",
};

describe("parseDonationInput", () => {
  it("normalizes email and applies defaults", () => {
    const input = parseDonationInput(valid);
    expect(input.donorEmail).toBe("donor@example.com");
    expect(input.frequency).toBe("one_time");
    expect(input.intent).toBe("sadaqah_jariyah");
    expect(input.anonymous).toBe(false);
  });

  it("rejects amounts below the minimum and above the ceiling", () => {
    expect(() => parseDonationInput({ ...valid, amountCents: 50 })).toThrow(DonationError);
    expect(() =>
      parseDonationInput({ ...valid, amountCents: MAX_DONATION_CENTS + 1 }),
    ).toThrow(DonationError);
  });

  it("rejects a missing or malformed email with a 400", () => {
    expect(() => parseDonationInput({ amountCents: 5000 })).toThrow(DonationError);
    try {
      parseDonationInput({ ...valid, donorEmail: "not-an-email" });
      throw new Error("should have thrown");
    } catch (err) {
      expect(err).toBeInstanceOf(DonationError);
      expect((err as DonationError).status).toBe(400);
    }
  });

  it("rejects unknown frequencies and intents", () => {
    expect(() => parseDonationInput({ ...valid, frequency: "weekly" })).toThrow(DonationError);
    expect(() => parseDonationInput({ ...valid, intent: "tips" })).toThrow(DonationError);
  });

  it("accepts monthly zakat with a dedication", () => {
    const input = parseDonationInput({
      ...valid,
      frequency: "monthly",
      intent: "zakat",
      dedication: "On behalf of my mother",
    });
    expect(input.frequency).toBe("monthly");
    expect(input.intent).toBe("zakat");
    expect(input.dedication).toBe("On behalf of my mother");
  });
});

describe("displayDonorName", () => {
  it("hides the name when the donor asked to be anonymous", () => {
    expect(displayDonorName({ anonymous: true, donorName: "Ali" })).toBe("Anonymous");
    expect(displayDonorName({ anonymous: false, donorName: null })).toBe("Anonymous");
    expect(displayDonorName({ anonymous: false, donorName: "Ali" })).toBe("Ali");
  });
});
