import { describe, expect, it } from "vitest";
import {
  formatMoney,
  formatMoneyCompact,
  parseAmountToCents,
  progressPercent,
  toCents,
  unitsCovered,
} from "./money";

describe("parseAmountToCents", () => {
  it("accepts plain, decimal and formatted input", () => {
    expect(parseAmountToCents("25")).toBe(2500);
    expect(parseAmountToCents("125.50")).toBe(12550);
    expect(parseAmountToCents(" $1,250 ")).toBe(125000);
    expect(parseAmountToCents("0.99")).toBe(99);
  });

  it("rejects anything that is not a usable amount", () => {
    expect(parseAmountToCents("")).toBeNull();
    expect(parseAmountToCents("abc")).toBeNull();
    expect(parseAmountToCents("-50")).toBeNull();
    expect(parseAmountToCents("10.999")).toBeNull(); // more precision than cents
    expect(parseAmountToCents("1e3")).toBeNull();
  });
});

describe("formatMoney", () => {
  it("drops cents for whole amounts and keeps them otherwise", () => {
    expect(formatMoney(2500)).toBe("$25");
    expect(formatMoney(12550)).toBe("$125.50");
  });

  it("shortens headline figures", () => {
    expect(formatMoneyCompact(8500000)).toBe("$85K");
  });
});

describe("progressPercent", () => {
  it("rounds to whole percent", () => {
    expect(progressPercent(4125000, 8500000)).toBe(49);
  });

  it("clamps over-funded projects and guards a zero goal", () => {
    expect(progressPercent(200, 100)).toBe(100);
    expect(progressPercent(100, 0)).toBe(0);
  });
});

describe("unitsCovered", () => {
  it("counts whole units only", () => {
    expect(unitsCovered(5000, 900)).toBe(5); // $50 buys 5 bags of cement
    expect(unitsCovered(500, 900)).toBe(0);
    expect(unitsCovered(5000, 0)).toBe(0);
  });
});

describe("toCents", () => {
  it("normalizes the string bigints node-postgres returns", () => {
    expect(toCents("8500000")).toBe(8500000);
    expect(toCents(8500000)).toBe(8500000);
    expect(toCents(null)).toBe(0);
    expect(toCents(undefined)).toBe(0);
  });
});
