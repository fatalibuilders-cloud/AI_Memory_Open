import { describe, expect, it } from "vitest";
import type { ProjectData } from "@/lib/project-schema";
import { computeCost } from "./index";

/**
 * Worked example — same 12 × 9 m bungalow as the materials engine.
 * Hand-checked amounts (full-contract rates, Fatali Builders 2026 card):
 *   excavation 37.8 m³ × 800            = 30,240
 *   ground slab 10.8 m³ × 17,000        = 183,600
 *   walling 165.3 m² × 2,000 (200 mm)   = 330,600
 *   hardcore 108 m² × 900               = 97,200
 */
const bungalow: ProjectData = {
  schemaVersion: 1,
  codeProfile: "kebs",
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

const find = (r: ReturnType<typeof computeCost>, sec: string, label: string) =>
  r.sections.find((s) => s.title === sec)!.items.find((i) => i.label.startsWith(label))!;

describe("cost engine — 12×9 bungalow worked example", () => {
  const result = computeCost(bungalow);

  it("prices excavation, slab, walling and hardcore per the rate card", () => {
    expect(find(result, "Substructure", "Foundation excavation").amountFull).toBe(30240);
    expect(find(result, "Concrete superstructure", "Ground slab").amountFull).toBe(183600);
    expect(find(result, "Walling", "200 mm blockwork").amountFull).toBe(330600);
    expect(find(result, "Substructure", "Hardcore").amountFull).toBe(97200);
  });

  it("labour-only mode is always cheaper than full contract", () => {
    expect(result.grandTotalLabour).toBeGreaterThan(0);
    expect(result.grandTotalLabour).toBeLessThan(result.grandTotalFull);
  });

  it("adds 5% contingency and sums the grand total", () => {
    expect(result.contingencyFull).toBe(Math.round(result.measuredWorksFull * 0.05));
    expect(result.grandTotalFull).toBe(result.measuredWorksFull + result.contingencyFull);
  });

  it("lands in a plausible range for a Kenyan bungalow of this size", () => {
    // 108 m² bungalow, covered scope only (structure, walls, roof, finishes,
    // doors/windows — services/ceilings/fittings excluded until later
    // releases): ≈ KES 20k-40k per m² → 2.2M-4.5M at 2026 rates.
    expect(result.grandTotalFull).toBeGreaterThan(2_200_000);
    expect(result.grandTotalFull).toBeLessThan(4_500_000);
  });

  it("omits zero-quantity items (no flat-roof or tile lines for this bungalow)", () => {
    const labels = result.sections.flatMap((s) => s.items.map((i) => i.label));
    expect(labels.some((l) => l.startsWith("Roof slab concrete"))).toBe(false);
    expect(labels.some((l) => l.startsWith("Ceramic floor tiles"))).toBe(false);
    expect(labels.some((l) => l.startsWith("Suspended slab"))).toBe(false);
  });
});

describe("cost engine — variants", () => {
  it("uses stone walling rate for natural stone", () => {
    const stone = computeCost({ ...bungalow, wallType: "natural_stone" });
    const wall = find(stone, "Walling", "Machine-cut stone walling");
    expect(wall.rateFull).toBe(2100);
  });

  it("prices the 150 mm blockwork rate when thickness is 150", () => {
    const thin = computeCost({ ...bungalow, wallThicknessMm: 150 });
    expect(find(thin, "Walling", "150 mm blockwork").rateFull).toBe(1900);
  });

  it("two-storey adds suspended slab and formwork costs", () => {
    const two = computeCost({ ...bungalow, floors: 2 });
    expect(find(two, "Concrete superstructure", "Suspended slab").amountFull).toBe(
      Math.round(16.2 * 17000),
    );
    expect(two.grandTotalFull).toBeGreaterThan(computeCost(bungalow).grandTotalFull);
  });

  it("flat roof swaps timber/sheets for slab + waterproofing", () => {
    const flat = computeCost({ ...bungalow, roofType: "flat_concrete" });
    const labels = flat.sections.flatMap((s) => s.items.map((i) => i.label));
    expect(labels.some((l) => l.startsWith("Roof slab concrete"))).toBe(true);
    expect(labels.some((l) => l.startsWith("Timber roof structure"))).toBe(false);
  });
});
