import { describe, expect, it } from "vitest";
import type { ProjectData } from "@/lib/project-schema";
import { computeMaterials } from "./residential";

/**
 * WORKED EXAMPLE 1 — 12 × 9 m bungalow (pending owner-engineer sign-off).
 * Hand calculations:
 *   perimeter = 2(12+9) = 42 m ; footprint = 108 m²
 *   excavation = 42 × 0.6 × 0.9 = 22.68 m³
 *   footing concrete = 42 × 0.6 × 0.2 = 5.04 m³
 *   ground slab = 108 × 0.1 = 10.8 m³
 *   external walls gross = 42 × 2.8 = 117.6 m² ; internal = 70.56 m²
 *   openings = 6×1.89 + 8×1.44 = 22.86 m²
 *   net wall area = 117.6 + 70.56 − 22.86 = 165.3 m²
 *   wall blocks = ceil(165.3 × 12.5 × 1.05) = ceil(2169.56) = 2170
 *   pitched roof area = 108 × 1.15 = 124.2 m² ; cover = 136.62 m²
 *   roof timber = ceil(124.2 × 5.5) = 684 m
 */
const bungalow: ProjectData = {
  schemaVersion: 1,
  codeProfile: "eurocode",
  country: "Kenya",
  floors: 1,
  footprintLengthM: 12,
  footprintWidthM: 9,
  floorHeightM: 2.8,
  wallType: "concrete_block",
  wallThicknessMm: 200,
  roofType: "gable_iron_sheets",
  doorsCount: 6,
  windowsCount: 8,
  plasterBothSides: true,
  paint: true,
  floorFinish: "screed",
  soilType: "unknown",
};

describe("residential materials engine — 12×9 bungalow worked example", () => {
  const result = computeMaterials(bungalow);
  const byTitle = (t: string) => result.sections.find((s) => s.title.startsWith(t))!;
  const item = (sec: string, label: string) =>
    byTitle(sec).items.find((i) => i.label === label)!.quantity;

  it("computes substructure quantities", () => {
    expect(item("Substructure", "Excavation")).toBeCloseTo(22.7, 1);
    expect(item("Substructure", "Footing concrete (1:3:6)")).toBeCloseTo(5, 1);
  });

  it("computes the ground slab", () => {
    expect(item("Ground floor slab", "Slab concrete (1:2:4, 100 mm)")).toBeCloseTo(10.8, 1);
  });

  it("computes net wall area and block count", () => {
    expect(item("Walling (external + internal)", "Net wall area")).toBeCloseTo(165.3, 1);
    expect(item("Walling (external + internal)", "Walling units")).toBe(2170);
  });

  it("computes the pitched roof", () => {
    expect(item("Pitched roof", "Roof area (pitched)")).toBeCloseTo(124.2, 1);
    expect(item("Pitched roof", "Roof timber (rafters, purlins, ties)")).toBe(684);
  });

  it("has no suspended slab section for a bungalow", () => {
    expect(result.sections.some((s) => s.title.startsWith("Suspended"))).toBe(false);
  });

  it("accumulates plausible totals", () => {
    expect(result.totals.cementBags).toBeGreaterThan(100); // bungalow of this size ≈ 150-300 bags
    expect(result.totals.cementBags).toBeLessThan(400);
    expect(result.totals.blocks).toBeGreaterThan(2170); // walls + foundation walling
    expect(result.totals.steelKg).toBeGreaterThan(0);
    expect(result.totals.paintLitres).toBe(Math.ceil(165.3 * 2 * 0.35));
  });
});

describe("residential materials engine — variants", () => {
  it("adds suspended slab and more steel for a two-storey house", () => {
    const twoStorey = computeMaterials({ ...bungalow, floors: 2 });
    const slab = twoStorey.sections.find((s) => s.title.startsWith("Suspended"))!;
    expect(slab.items[0].quantity).toBeCloseTo(108 * 0.15, 1); // 16.2 m³
    expect(twoStorey.totals.steelKg).toBeGreaterThan(computeMaterials(bungalow).totals.steelKg);
  });

  it("switches to concrete roof quantities for flat_concrete", () => {
    const flat = computeMaterials({ ...bungalow, roofType: "flat_concrete" });
    expect(flat.sections.some((s) => s.title === "Flat concrete roof")).toBe(true);
    expect(flat.totals.roofCoverM2).toBe(0);
    expect(flat.totals.roofTimberM).toBe(0);
  });

  it("swaps screed for tiles when floorFinish=ceramic_tiles", () => {
    const tiled = computeMaterials({ ...bungalow, floorFinish: "ceramic_tiles" });
    const finishes = tiled.sections.find((s) => s.title === "Finishes & openings")!;
    expect(finishes.items.some((i) => i.label.startsWith("Ceramic tiles"))).toBe(true);
    expect(finishes.items.some((i) => i.label.startsWith("Floor screed"))).toBe(false);
  });

  it("drops plaster items when plasterBothSides=false but still paints the walls", () => {
    const noPlaster = computeMaterials({ ...bungalow, plasterBothSides: false });
    const finishes = noPlaster.sections.find((s) => s.title === "Finishes & openings")!;
    expect(finishes.items.some((i) => i.label.startsWith("Plaster area"))).toBe(false);
    expect(noPlaster.totals.paintLitres).toBe(Math.ceil(165.3 * 0.35));
  });
});
