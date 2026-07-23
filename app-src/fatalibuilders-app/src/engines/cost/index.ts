/**
 * Cost estimation engine — Release 1.0 (CORE-5.1).
 *
 * Prices the measured quantities from the materials engine using the
 * owner's work-item rate card, producing a BOQ-style estimate
 * (Item | Qty | Unit | Rate | Amount, grouped in elements with a grand
 * summary) modeled on Fatali Builders' professional BOQ format.
 *
 * Two pricing modes, exactly as the rate card defines:
 *  - "labour":  client supplies materials, contractor charges labour only
 *  - "full":    full contract — labour + materials
 */

import type { ProjectData } from "@/lib/project-schema";
import { computeMaterials, type Measures } from "../materials/residential";

export const COST_ENGINE_VERSION = "0.1.0";

/**
 * Rate card: Fatali Builders Construction Rates 2026 (KES), provided by
 * Eng Ali Ahmed 2026-07-23. [labourOnly, labourAndMaterial] per unit.
 * Users can adjust rates per project in a later story; these are the
 * company baseline.
 */
export const RATES_KES = {
  siteClearanceM2: [100, 100],
  settingOutItem: [8000, 8000],
  excavationM3: [550, 800],
  backfillM3: [420, 700],
  hardcoreM2: [180, 900],
  blindingM2: [250, 1000],
  dpmM2: [120, 250],
  concreteFoundationM3: [6000, 18000],
  concreteSlabM3: [5200, 17000],
  concreteColumnsM3: [6000, 19000],
  concreteBeamsM3: [5200, 18500],
  reinforcementKg: [50, 180],
  formworkSlabsM2: [1000, 1200],
  blockwork200M2: [800, 2000],
  blockwork150M2: [750, 1900],
  stoneWallingM2: [850, 2100],
  lintelM: [500, 1600],
  timberRoofTrussM2: [1200, 4200],
  roofSheetsM2: [500, 1900],
  internalPlasterM2: [400, 750],
  externalPlasterM2: [450, 850],
  paintingInternalM2: [250, 450],
  paintingExternalM2: [300, 550],
  floorScreedM2: [300, 650],
  ceramicTilesM2: [550, 1800],
  woodenDoorNo: [2500, 15000],
  casementWindowM2: [1500, 6500],
  waterproofingM2: [850, 1200],
} as const;

export const CONTINGENCY_RATE = 0.05; // provisional sum, % of measured works (BOQ practice)

export type PricingMode = "labour" | "full";

export interface CostItem {
  label: string;
  quantity: number;
  unit: string;
  rateLabour: number;
  rateFull: number;
  amountLabour: number;
  amountFull: number;
}

export interface CostSection {
  title: string;
  items: CostItem[];
  subtotalLabour: number;
  subtotalFull: number;
}

export interface CostResult {
  engineVersion: string;
  currency: "KES";
  sections: CostSection[];
  measuredWorksLabour: number;
  measuredWorksFull: number;
  contingencyLabour: number;
  contingencyFull: number;
  grandTotalLabour: number;
  grandTotalFull: number;
}

const r0 = (n: number) => Math.round(n);

function item(
  label: string,
  quantity: number,
  unit: string,
  [rateLabour, rateFull]: readonly [number, number],
): CostItem {
  const q = Math.round(quantity * 100) / 100;
  return {
    label,
    quantity: q,
    unit,
    rateLabour,
    rateFull,
    amountLabour: r0(q * rateLabour),
    amountFull: r0(q * rateFull),
  };
}

function section(title: string, items: CostItem[]): CostSection {
  const nonZero = items.filter((i) => i.quantity > 0);
  return {
    title,
    items: nonZero,
    subtotalLabour: nonZero.reduce((s, i) => s + i.amountLabour, 0),
    subtotalFull: nonZero.reduce((s, i) => s + i.amountFull, 0),
  };
}

export function computeCost(d: ProjectData): CostResult {
  const m: Measures = computeMaterials(d).measures;
  const R = RATES_KES;

  const wallRate = m.wallIsStone
    ? R.stoneWallingM2
    : m.wallThicknessMm <= 150
      ? R.blockwork150M2
      : R.blockwork200M2;

  const sections: CostSection[] = [
    section("Preliminaries", [
      item("Site clearance", m.footprintM2 * 1.5, "m²", R.siteClearanceM2),
      item("Setting out", 1, "item", R.settingOutItem),
    ]),
    section("Substructure", [
      item("Foundation excavation", m.excavationM3, "m³", R.excavationM3),
      item("Backfilling", m.backfillM3, "m³", R.backfillM3),
      item("Hardcore filling 150 mm", m.hardcoreM2, "m²", R.hardcoreM2),
      item("Sand blinding", m.blindingM2, "m²", R.blindingM2),
      item("Damp-proof membrane", m.dpmM2, "m²", R.dpmM2),
      item("Foundation concrete (1:3:6)", m.footingConcreteM3, "m³", R.concreteFoundationM3),
      item("Foundation walling", m.foundationWallM2, "m²", wallRate),
    ]),
    section("Concrete superstructure", [
      item("Ground slab concrete", m.groundSlabM3, "m³", R.concreteSlabM3),
      item("Suspended slab concrete", m.suspendedSlabM3, "m³", R.concreteSlabM3),
      item("Slab formwork", m.slabFormworkM2, "m²", R.formworkSlabsM2),
      item("Ring beam concrete", m.ringBeamM3, "m³", R.concreteBeamsM3),
      item("Column concrete", m.columnConcreteM3, "m³", R.concreteColumnsM3),
      item("Reinforcement (supply, cut, bend, fix)", m.steelKg, "kg", R.reinforcementKg),
    ]),
    section("Walling", [
      item(
        m.wallIsStone ? "Machine-cut stone walling" : `${m.wallThicknessMm} mm blockwork`,
        m.wallNetM2,
        "m²",
        wallRate,
      ),
      item("Lintels", m.lintelM, "m", R.lintelM),
    ]),
    section("Roofing", [
      item("Timber roof structure", m.pitchedRoofM2, "m²", R.timberRoofTrussM2),
      item("Roof covering installation", m.roofCoverM2, "m²", R.roofSheetsM2),
      item("Roof slab concrete (flat roof)", m.flatRoofM3, "m³", R.concreteSlabM3),
      item("Waterproofing (flat roof)", m.flatRoofWaterproofM2, "m²", R.waterproofingM2),
    ]),
    section("Finishes", [
      item("External plaster", m.plasterExtM2, "m²", R.externalPlasterM2),
      item("Internal plaster", m.plasterIntM2, "m²", R.internalPlasterM2),
      item("External painting", m.paintExtM2, "m²", R.paintingExternalM2),
      item("Internal painting (3 coats)", m.paintIntM2, "m²", R.paintingInternalM2),
      item("Floor screed", m.screedM2, "m²", R.floorScreedM2),
      item("Ceramic floor tiles", m.tilesM2, "m²", R.ceramicTilesM2),
    ]),
    section("Doors & windows", [
      item("Wooden doors (supply & fix)", m.doorsNo, "no.", R.woodenDoorNo),
      item("Casement windows", m.windowsM2, "m²", R.casementWindowM2),
    ]),
  ].filter((s) => s.items.length > 0);

  const measuredWorksLabour = sections.reduce((s, x) => s + x.subtotalLabour, 0);
  const measuredWorksFull = sections.reduce((s, x) => s + x.subtotalFull, 0);
  const contingencyLabour = r0(measuredWorksLabour * CONTINGENCY_RATE);
  const contingencyFull = r0(measuredWorksFull * CONTINGENCY_RATE);

  return {
    engineVersion: COST_ENGINE_VERSION,
    currency: "KES",
    sections,
    measuredWorksLabour,
    measuredWorksFull,
    contingencyLabour,
    contingencyFull,
    grandTotalLabour: measuredWorksLabour + contingencyLabour,
    grandTotalFull: measuredWorksFull + contingencyFull,
  };
}

export function formatKES(n: number): string {
  return `KES ${n.toLocaleString("en-KE")}`;
}
