import { describe, expect, it } from "vitest";
import type { ProjectData } from "@/lib/project-schema";
import { computeLabor } from "./index";

/**
 * Worked example — same 12 × 9 m bungalow.
 * Hand checks:
 *   Walling: 165.3 m² ÷ (9 m²/mason-day × 2 masons) = 9.18 → 10 days
 *     crew cost/day = 2×1500 + 2×600 = 4,200 → phase cost 42,000 (laborer 600)
 *   Excavation: 37.8 m³ ÷ (2 m³/day × 4 laborers) = 4.72 → 5 days
 *   Painting: (both faces of 165.3 m² net) ÷ (40 × 2) → 331 m²/80 = 4.13 → 5 days
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

const get = (r: ReturnType<typeof computeLabor>, name: string) =>
  r.phases.find((p) => p.name === name)!;

describe("labor engine — 12×9 bungalow worked example", () => {
  const result = computeLabor(bungalow);

  it("computes walling duration and cost from day rates", () => {
    const walling = get(result, "Walling");
    expect(walling.durationDays).toBe(10);
    expect(walling.laborCostKES).toBe(10 * (2 * 1500 + 2 * 600)); // 42,000 (laborer 600)
  });

  it("computes excavation duration", () => {
    expect(get(result, "Excavation & earthworks").durationDays).toBe(5);
  });

  it("computes painting duration", () => {
    expect(get(result, "Painting").durationDays).toBe(5);
  });

  it("produces a plausible overall duration for a bungalow", () => {
    expect(result.calendarWeeks).toBeGreaterThanOrEqual(5);
    expect(result.calendarWeeks).toBeLessThanOrEqual(16);
    expect(result.workingDays).toBeLessThanOrEqual(
      result.phases.reduce((s, p) => s + p.durationDays, 0),
    );
  });

  it("adds weekly engineer supervision to the labor cost", () => {
    expect(result.supervisionDays).toBe(result.calendarWeeks);
    const phasesCost = result.phases.reduce((s, p) => s + p.laborCostKES, 0);
    expect(result.totalLaborCostKES).toBe(phasesCost + result.supervisionDays * 5000);
  });

  it("has no roofing phase for a flat concrete roof", () => {
    const flat = computeLabor({ ...bungalow, roofType: "flat_concrete" });
    expect(flat.phases.some((p) => p.name === "Roofing")).toBe(false);
  });

  it("two-storey takes longer than the bungalow", () => {
    const two = computeLabor({ ...bungalow, floors: 2 });
    expect(two.workingDays).toBeGreaterThan(result.workingDays);
  });
});
