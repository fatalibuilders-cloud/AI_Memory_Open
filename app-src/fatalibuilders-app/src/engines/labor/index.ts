/**
 * Labor & time estimation engine — Release 1.0 (CORE-5.2).
 *
 * Estimates crew composition, duration and labor cost per construction
 * phase from the materials engine's measures.
 *
 * DAY_RATES_KES come from the owner's AP Mosque weekly work log
 * (2026-07-23). Productivity norms are common Kenyan estimating values —
 * flagged for owner-engineer validation like the materials ASSUMPTIONS.
 */

import type { ProjectData } from "@/lib/project-schema";
import { computeMaterials, type Measures } from "../materials/residential";

export const LABOR_ENGINE_VERSION = "0.1.0";

/** KES per day. Mason/laborer/engineer from the owner's work log; carpenter/painter pending owner confirmation. */
export const DAY_RATES_KES = {
  mason: 1500,
  laborer: 1200,
  carpenter: 1500, // assumed = mason rate, pending owner confirmation
  painter: 1300, // assumed, pending owner confirmation
  engineer: 5000,
} as const;

export type Role = keyof typeof DAY_RATES_KES;

export const LABOR_ASSUMPTIONS = {
  EXCAVATION_M3_PER_LABORER_DAY: 2.0,
  CONCRETE_M3_PER_CREW_DAY: 8.0, // crew: 1 mason + 5 laborers
  WALLING_M2_PER_MASON_DAY: 9.0, // each mason paired with 1 laborer
  ROOFING_M2_PER_CREW_DAY: 25.0, // crew: 2 carpenters + 2 laborers
  PLASTER_M2_PER_MASON_DAY: 12.0, // each mason paired with 1 laborer
  PAINTING_M2_PER_PAINTER_DAY: 40.0,
  SCREED_M2_PER_MASON_DAY: 20.0,
  PARALLEL_FACTOR: 0.85, // phases overlap ≈15% on a well-run site
  WORKDAYS_PER_WEEK: 6,
  ENGINEER_DAYS_PER_WEEK: 1, // supervision visit cadence
} as const;

export interface CrewMember {
  role: Role;
  count: number;
}

export interface LaborPhase {
  name: string;
  crew: CrewMember[];
  durationDays: number;
  laborCostKES: number;
}

export interface LaborResult {
  engineVersion: string;
  phases: LaborPhase[];
  peakCrew: number;
  workingDays: number;
  calendarWeeks: number;
  supervisionDays: number;
  totalLaborCostKES: number;
  dayRates: typeof DAY_RATES_KES;
  assumptions: typeof LABOR_ASSUMPTIONS;
}

const dayCost = (crew: CrewMember[]) =>
  crew.reduce((s, c) => s + c.count * DAY_RATES_KES[c.role], 0);

function phase(name: string, crew: CrewMember[], rawDays: number): LaborPhase | null {
  if (rawDays <= 0) return null;
  const durationDays = Math.max(1, Math.ceil(rawDays));
  return { name, crew, durationDays, laborCostKES: durationDays * dayCost(crew) };
}

export function computeLabor(d: ProjectData): LaborResult {
  const A = LABOR_ASSUMPTIONS;
  const m: Measures = computeMaterials(d).measures;

  const phases: LaborPhase[] = [];
  const push = (p: LaborPhase | null) => p && phases.push(p);

  // Substructure: excavation by laborers, then foundation concrete + walling
  const excLaborers = 4;
  push(
    phase(
      "Excavation & earthworks",
      [{ role: "laborer", count: excLaborers }],
      m.excavationM3 / (A.EXCAVATION_M3_PER_LABORER_DAY * excLaborers),
    ),
  );
  const foundationConcrete = m.footingConcreteM3 + m.groundSlabM3;
  push(
    phase(
      "Foundation & ground slab",
      [
        { role: "mason", count: 1 },
        { role: "laborer", count: 5 },
      ],
      foundationConcrete / A.CONCRETE_M3_PER_CREW_DAY +
        m.foundationWallM2 / (A.WALLING_M2_PER_MASON_DAY * 1),
    ),
  );

  // Walling: 2 masons + 2 laborers
  const wallMasons = 2;
  push(
    phase(
      "Walling",
      [
        { role: "mason", count: wallMasons },
        { role: "laborer", count: wallMasons },
      ],
      m.wallNetM2 / (A.WALLING_M2_PER_MASON_DAY * wallMasons),
    ),
  );

  // Concrete frame + suspended slabs
  const frameConcrete = m.ringBeamM3 + m.columnConcreteM3 + m.suspendedSlabM3 + m.flatRoofM3;
  push(
    phase(
      "Concrete frame & slabs",
      [
        { role: "mason", count: 1 },
        { role: "laborer", count: 5 },
      ],
      frameConcrete / A.CONCRETE_M3_PER_CREW_DAY,
    ),
  );

  // Roofing (pitched only — flat roof handled in concrete phase)
  push(
    phase(
      "Roofing",
      [
        { role: "carpenter", count: 2 },
        { role: "laborer", count: 2 },
      ],
      m.pitchedRoofM2 / A.ROOFING_M2_PER_CREW_DAY,
    ),
  );

  // Plastering & screed: 2 masons + 2 laborers
  const plasterM2 = m.plasterExtM2 + m.plasterIntM2;
  const plasterMasons = 2;
  push(
    phase(
      "Plastering & floor screed",
      [
        { role: "mason", count: plasterMasons },
        { role: "laborer", count: plasterMasons },
      ],
      plasterM2 / (A.PLASTER_M2_PER_MASON_DAY * plasterMasons) +
        m.screedM2 / (A.SCREED_M2_PER_MASON_DAY * plasterMasons),
    ),
  );

  // Painting
  const paintM2 = m.paintExtM2 + m.paintIntM2;
  push(
    phase("Painting", [{ role: "painter", count: 2 }], paintM2 / (A.PAINTING_M2_PER_PAINTER_DAY * 2)),
  );

  const sequentialDays = phases.reduce((s, p) => s + p.durationDays, 0);
  const workingDays = Math.ceil(sequentialDays * A.PARALLEL_FACTOR);
  const calendarWeeks = Math.ceil(workingDays / A.WORKDAYS_PER_WEEK);
  const supervisionDays = calendarWeeks * A.ENGINEER_DAYS_PER_WEEK;
  const supervisionCost = supervisionDays * DAY_RATES_KES.engineer;
  const peakCrew = Math.max(...phases.map((p) => p.crew.reduce((s, c) => s + c.count, 0)));
  const totalLaborCostKES =
    phases.reduce((s, p) => s + p.laborCostKES, 0) + supervisionCost;

  return {
    engineVersion: LABOR_ENGINE_VERSION,
    phases,
    peakCrew,
    workingDays,
    calendarWeeks,
    supervisionDays,
    totalLaborCostKES,
    dayRates: DAY_RATES_KES,
    assumptions: A,
  };
}
