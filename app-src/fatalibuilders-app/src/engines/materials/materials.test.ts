import { describe, expect, it } from "vitest";
import { concreteMaterials, concreteVolume, wallBlocks } from "./index";

describe("concreteVolume", () => {
  it("computes a slab volume", () => {
    expect(concreteVolume(10, 5, 0.15)).toBe(7.5);
  });

  it("rejects non-positive dimensions", () => {
    expect(() => concreteVolume(0, 5, 0.15)).toThrow(RangeError);
    expect(() => concreteVolume(10, -1, 0.15)).toThrow(RangeError);
    expect(() => concreteVolume(10, 5, NaN)).toThrow(RangeError);
  });
});

describe("concreteMaterials (1:2:4 nominal mix)", () => {
  // Worked example: 1 m³ of 1:2:4 concrete → dry volume 1.54 m³,
  // cement 1/7 × 1.54 = 0.22 m³ → 0.22/0.0347 = 6.34 → 7 bags,
  // sand 2/7 × 1.54 = 0.44 m³, ballast 4/7 × 1.54 = 0.88 m³.
  // Pending owner-engineer sign-off as a validated example (CORE-5.0).
  it("matches the standard 1 m³ worked example", () => {
    const result = concreteMaterials(1);
    expect(result.cementBags).toBe(7);
    expect(result.sandM3).toBeCloseTo(0.44, 2);
    expect(result.ballastM3).toBeCloseTo(0.88, 2);
  });

  it("scales linearly with volume", () => {
    const one = concreteMaterials(1);
    const ten = concreteMaterials(10);
    expect(ten.sandM3).toBeCloseTo(one.sandM3 * 10, 1);
  });

  it("rejects non-positive volume", () => {
    expect(() => concreteMaterials(0)).toThrow(RangeError);
  });
});

describe("wallBlocks", () => {
  it("computes blocks for 100 m² with defaults (12.5/m², 5% waste)", () => {
    expect(wallBlocks(100)).toBe(1313);
  });

  it("honours custom density and waste", () => {
    expect(wallBlocks(100, { unitsPerM2: 10, wastePct: 0 })).toBe(1000);
  });

  it("rejects non-positive area", () => {
    expect(() => wallBlocks(-5)).toThrow(RangeError);
  });
});
