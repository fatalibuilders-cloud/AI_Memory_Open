import { describe, expect, it } from "vitest";
import type { ProjectData } from "@/lib/project-schema";
import { projectDataSchema } from "@/lib/project-schema";
import { computeMaterials } from "./materials/residential";
import { computeCost } from "./cost";
import { computeLabor } from "./labor";

/**
 * CORE-5.3 — Engine hardening. Proves the three engines are robust across
 * the full valid input range (bounded by the schema), never produce NaN /
 * Infinity / negative quantities, and are deterministic.
 */

const base: ProjectData = projectDataSchema.parse({
  footprintLengthM: 8,
  footprintWidthM: 6,
});

const tiny: ProjectData = projectDataSchema.parse({
  footprintLengthM: 3,
  footprintWidthM: 3,
  floors: 1,
  doorsCount: 1,
  windowsCount: 1,
  plasterBothSides: false,
  paint: false,
});

const large: ProjectData = projectDataSchema.parse({
  footprintLengthM: 100,
  footprintWidthM: 100,
  floors: 4,
  doorsCount: 100,
  windowsCount: 200,
  wallThicknessMm: 230,
});

const cases: Array<[string, ProjectData]> = [
  ["base", base],
  ["tiny", tiny],
  ["large", large],
];

function everyNumberFinite(obj: unknown, path = "root"): string[] {
  const bad: string[] = [];
  const walk = (v: unknown, p: string) => {
    if (typeof v === "number") {
      if (!Number.isFinite(v)) bad.push(`${p}=${v}`);
    } else if (Array.isArray(v)) {
      v.forEach((x, i) => walk(x, `${p}[${i}]`));
    } else if (v && typeof v === "object") {
      for (const [k, val] of Object.entries(v)) walk(val, `${p}.${k}`);
    }
  };
  walk(obj, path);
  return bad;
}

describe("CORE-5.3 engine hardening", () => {
  for (const [name, data] of cases) {
    it(`materials engine: finite, non-negative quantities (${name})`, () => {
      const r = computeMaterials(data);
      expect(everyNumberFinite(r)).toEqual([]);
      for (const s of r.sections)
        for (const it of s.items) expect(it.quantity).toBeGreaterThanOrEqual(0);
      for (const v of Object.values(r.totals)) expect(v).toBeGreaterThanOrEqual(0);
    });

    it(`cost engine: finite amounts, labour ≤ full (${name})`, () => {
      const r = computeCost(data);
      expect(everyNumberFinite(r)).toEqual([]);
      expect(r.grandTotalLabour).toBeLessThanOrEqual(r.grandTotalFull);
      for (const s of r.sections) {
        for (const it of s.items) {
          expect(it.amountLabour).toBeGreaterThanOrEqual(0);
          expect(it.amountLabour).toBeLessThanOrEqual(it.amountFull);
        }
      }
    });

    it(`labor engine: finite, positive durations, sensible crew (${name})`, () => {
      const r = computeLabor(data);
      expect(everyNumberFinite(r)).toEqual([]);
      expect(r.workingDays).toBeGreaterThan(0);
      expect(r.peakCrew).toBeGreaterThan(0);
      for (const p of r.phases) expect(p.durationDays).toBeGreaterThanOrEqual(1);
    });
  }

  it("engines are deterministic (same input → identical output)", () => {
    expect(JSON.stringify(computeMaterials(base))).toBe(JSON.stringify(computeMaterials(base)));
    expect(JSON.stringify(computeCost(base))).toBe(JSON.stringify(computeCost(base)));
    expect(JSON.stringify(computeLabor(base))).toBe(JSON.stringify(computeLabor(base)));
  });

  it("larger buildings cost and take more than smaller ones (monotonic)", () => {
    expect(computeCost(large).grandTotalFull).toBeGreaterThan(computeCost(tiny).grandTotalFull);
    expect(computeLabor(large).workingDays).toBeGreaterThan(computeLabor(tiny).workingDays);
    expect(computeMaterials(large).totals.blocks).toBeGreaterThan(
      computeMaterials(tiny).totals.blocks,
    );
  });

  it("every result carries an engine version stamp", () => {
    expect(computeMaterials(base).engineVersion).toMatch(/^\d+\.\d+\.\d+$/);
    expect(computeCost(base).engineVersion).toMatch(/^\d+\.\d+\.\d+$/);
    expect(computeLabor(base).engineVersion).toMatch(/^\d+\.\d+\.\d+$/);
  });
});
