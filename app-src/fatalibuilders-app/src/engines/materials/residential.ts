/**
 * Residential materials quantities engine — Release 1.0 (CORE-5.0).
 *
 * Computes an itemized bill of quantities from the unified project data.
 * Every constant lives in ASSUMPTIONS below with a name, value and unit so
 * the owner-engineer can review each one. Values follow common Kenyan
 * estimating practice under Eurocode/BS conventions.
 *
 * STATUS: pending owner-engineer validation of ASSUMPTIONS and the worked
 * examples in residential.test.ts (CORE-5.0 acceptance).
 */

import type { ProjectData } from "@/lib/project-schema";
import { concreteMaterials } from "./index";

export const ENGINE_VERSION = "0.2.1";

export const ASSUMPTIONS = {
  // Substructure
  FOUNDATION_DEPTH_M: 1.5, // strip foundation depth — owner-engineer correction 2026-07-23 (was 0.9)
  FOOTING_WIDTH_M: 0.6,
  FOOTING_THICKNESS_M: 0.2, // mass concrete strip footing (1:3:6)
  HARDCORE_THICKNESS_M: 0.15,
  BLINDING_THICKNESS_M: 0.05, // sand blinding under slab
  // Ground & upper slabs
  GROUND_SLAB_THICKNESS_M: 0.1, // 1:2:4 with BRC mesh
  UPPER_SLAB_THICKNESS_M: 0.15, // suspended slab 1:2:4
  SLAB_REBAR_KG_PER_M3: 100, // upper slabs reinforcement density
  BRC_LAP_ALLOWANCE: 1.1, // +10% laps on mesh area
  // Walls
  INTERNAL_WALL_FACTOR: 0.6, // internal wall area ≈ 60% of external gross
  BLOCKS_PER_M2: 12.5, // 400×200 face size incl. joints
  BLOCK_WASTE: 1.05, // +5%
  MORTAR_JOINT_FRACTION: 0.15, // mortar ≈ 15% of wall volume (1:4 mix)
  DOOR_AREA_M2: 0.9 * 2.1,
  WINDOW_AREA_M2: 1.2 * 1.2,
  // Ring beam & columns
  RING_BEAM_SECTION_M2: 0.2 * 0.2, // 200×200
  RING_BEAM_REBAR_KG_PER_M: 4 * 0.888 * 1.3, // 4Y12 + 30% stirrups
  COLUMN_SPACING_M: 4, // one 200×200 column every ~4 m of perimeter
  COLUMN_SECTION_M2: 0.2 * 0.2,
  COLUMN_REBAR_KG_PER_M: 4 * 0.888 * 1.3,
  // Roof
  PITCH_AREA_FACTOR: 1.15, // pitched roof area vs footprint (≈20-25° pitch)
  ROOF_COVER_WASTE: 1.1, // +10% laps/waste on sheets or tiles
  ROOF_TIMBER_M_PER_M2: 5.5, // running metres of timber per m² pitched roof
  FLAT_ROOF_SCREED_THICKNESS_M: 0.032,
  // Finishes
  PLASTER_THICKNESS_M: 0.0175, // owner-engineer spec 2026-07-23: 15-20 mm per face (midpoint used), 1:4 mortar
  PAINT_L_PER_M2: 0.35, // two coats
  SCREED_THICKNESS_M: 0.032, // 1:3 floor screed
  TILE_ADHESIVE_KG_PER_M2: 5,
  // Mortar mixes (cement bags & sand per m³ of mortar)
  MORTAR_1_4_CEMENT_BAGS_PER_M3: 9.7,
  MORTAR_1_4_SAND_M3_PER_M3: 1.06,
  MORTAR_1_3_CEMENT_BAGS_PER_M3: 12.2,
  MORTAR_1_3_SAND_M3_PER_M3: 1.0,
} as const;

export interface QuantityItem {
  label: string;
  quantity: number;
  unit: string;
}

export interface MaterialsSection {
  title: string;
  items: QuantityItem[];
}

export interface MaterialsTotals {
  cementBags: number;
  sandM3: number;
  ballastM3: number;
  blocks: number;
  steelKg: number;
  brcMeshM2: number;
  roofTimberM: number;
  roofCoverM2: number;
  paintLitres: number;
}

/** Machine-readable measured quantities — consumed by the cost engine. */
export interface Measures {
  footprintM2: number;
  perimeterM: number;
  excavationM3: number;
  backfillM3: number;
  footingConcreteM3: number;
  foundationWallM2: number;
  hardcoreM2: number;
  blindingM2: number;
  dpmM2: number;
  groundSlabM3: number;
  suspendedSlabM3: number;
  slabFormworkM2: number;
  ringBeamM3: number;
  columnConcreteM3: number;
  steelKg: number;
  wallNetM2: number;
  wallThicknessMm: number;
  wallIsStone: boolean;
  lintelM: number;
  pitchedRoofM2: number;
  roofCoverM2: number;
  flatRoofM3: number;
  flatRoofWaterproofM2: number;
  plasterExtM2: number;
  plasterIntM2: number;
  paintExtM2: number;
  paintIntM2: number;
  screedM2: number;
  tilesM2: number;
  doorsNo: number;
  windowsM2: number;
}

export interface MaterialsResult {
  engineVersion: string;
  sections: MaterialsSection[];
  totals: MaterialsTotals;
  measures: Measures;
  assumptions: typeof ASSUMPTIONS;
}

const r1 = (n: number) => Math.round(n * 10) / 10;

export function computeMaterials(d: ProjectData): MaterialsResult {
  const A = ASSUMPTIONS;
  const L = d.footprintLengthM;
  const W = d.footprintWidthM;
  const perimeter = 2 * (L + W);
  const footprint = L * W;
  const flatRoof = d.roofType === "flat_concrete";

  const totals: MaterialsTotals = {
    cementBags: 0,
    sandM3: 0,
    ballastM3: 0,
    blocks: 0,
    steelKg: 0,
    brcMeshM2: 0,
    roofTimberM: 0,
    roofCoverM2: 0,
    paintLitres: 0,
  };
  const addConcrete = (
    volumeM3: number,
    mix?: { cement: number; sand: number; ballast: number },
  ) => {
    const m = concreteMaterials(volumeM3, mix);
    totals.cementBags += m.cementBags;
    totals.sandM3 += m.sandM3;
    totals.ballastM3 += m.ballastM3;
    return m;
  };
  const addMortar = (volumeM3: number, mix: "1:4" | "1:3") => {
    const bags =
      volumeM3 *
      (mix === "1:4" ? A.MORTAR_1_4_CEMENT_BAGS_PER_M3 : A.MORTAR_1_3_CEMENT_BAGS_PER_M3);
    const sand =
      volumeM3 * (mix === "1:4" ? A.MORTAR_1_4_SAND_M3_PER_M3 : A.MORTAR_1_3_SAND_M3_PER_M3);
    totals.cementBags += Math.ceil(bags);
    totals.sandM3 += sand;
    return { bags: Math.ceil(bags), sand };
  };

  // ---- Substructure ----
  const excavation = perimeter * A.FOOTING_WIDTH_M * A.FOUNDATION_DEPTH_M;
  const footingVol = perimeter * A.FOOTING_WIDTH_M * A.FOOTING_THICKNESS_M;
  const footing = addConcrete(footingVol, { cement: 1, sand: 3, ballast: 6 });
  const foundationWallHeight = A.FOUNDATION_DEPTH_M - A.FOOTING_THICKNESS_M;
  const foundationWallArea = perimeter * foundationWallHeight;
  const foundationBlocks = Math.ceil(foundationWallArea * A.BLOCKS_PER_M2 * A.BLOCK_WASTE);
  totals.blocks += foundationBlocks;
  const foundationMortar = addMortar(
    foundationWallArea * (d.wallThicknessMm / 1000) * A.MORTAR_JOINT_FRACTION,
    "1:4",
  );
  const hardcore = footprint * A.HARDCORE_THICKNESS_M;
  const blindingSand = footprint * A.BLINDING_THICKNESS_M;
  totals.sandM3 += blindingSand;

  const substructure: MaterialsSection = {
    title: "Substructure (strip foundation)",
    items: [
      { label: "Excavation", quantity: r1(excavation), unit: "m³" },
      { label: "Footing concrete (1:3:6)", quantity: r1(footingVol), unit: "m³" },
      { label: "→ Cement", quantity: footing.cementBags, unit: "bags (50 kg)" },
      { label: "→ Sand", quantity: r1(footing.sandM3), unit: "m³" },
      { label: "→ Ballast", quantity: r1(footing.ballastM3), unit: "m³" },
      { label: "Foundation walling blocks", quantity: foundationBlocks, unit: "blocks" },
      { label: "→ Mortar cement (1:4)", quantity: foundationMortar.bags, unit: "bags" },
      { label: "Hardcore fill", quantity: r1(hardcore), unit: "m³" },
      { label: "Sand blinding", quantity: r1(blindingSand), unit: "m³" },
      { label: "Damp-proof membrane", quantity: r1(footprint * 1.1), unit: "m²" },
    ],
  };

  // ---- Ground slab ----
  const groundSlabVol = footprint * A.GROUND_SLAB_THICKNESS_M;
  const groundSlab = addConcrete(groundSlabVol);
  const brc = footprint * A.BRC_LAP_ALLOWANCE;
  totals.brcMeshM2 += brc;
  const groundSlabSection: MaterialsSection = {
    title: "Ground floor slab",
    items: [
      { label: "Slab concrete (1:2:4, 100 mm)", quantity: r1(groundSlabVol), unit: "m³" },
      { label: "→ Cement", quantity: groundSlab.cementBags, unit: "bags (50 kg)" },
      { label: "→ Sand", quantity: r1(groundSlab.sandM3), unit: "m³" },
      { label: "→ Ballast", quantity: r1(groundSlab.ballastM3), unit: "m³" },
      { label: "BRC mesh (A142, incl. laps)", quantity: r1(brc), unit: "m²" },
    ],
  };

  // ---- Walls ----
  const wallHeight = d.floorHeightM;
  const externalGross = perimeter * wallHeight * d.floors;
  const internalGross = externalGross * A.INTERNAL_WALL_FACTOR;
  const openings = d.doorsCount * A.DOOR_AREA_M2 + d.windowsCount * A.WINDOW_AREA_M2;
  const netWallArea = Math.max(externalGross + internalGross - openings, 0);
  const wallBlocksCount = Math.ceil(netWallArea * A.BLOCKS_PER_M2 * A.BLOCK_WASTE);
  totals.blocks += wallBlocksCount;
  const wallMortarVol = netWallArea * (d.wallThicknessMm / 1000) * A.MORTAR_JOINT_FRACTION;
  const wallMortar = addMortar(wallMortarVol, "1:4");
  const walls: MaterialsSection = {
    title: "Walling (external + internal)",
    items: [
      { label: "Net wall area", quantity: r1(netWallArea), unit: "m²" },
      { label: "Walling units", quantity: wallBlocksCount, unit: "blocks" },
      { label: "→ Mortar cement (1:4)", quantity: wallMortar.bags, unit: "bags" },
      { label: "→ Mortar sand", quantity: r1(wallMortar.sand), unit: "m³" },
    ],
  };

  // ---- Ring beam & columns ----
  const ringBeamVol = perimeter * A.RING_BEAM_SECTION_M2 * d.floors;
  const ringBeam = addConcrete(ringBeamVol);
  const ringBeamSteel = perimeter * A.RING_BEAM_REBAR_KG_PER_M * d.floors;
  const columnCount = Math.ceil(perimeter / A.COLUMN_SPACING_M);
  const columnHeight = wallHeight * d.floors;
  const columnVol = columnCount * A.COLUMN_SECTION_M2 * columnHeight;
  const columns = addConcrete(columnVol);
  const columnSteel = columnCount * columnHeight * A.COLUMN_REBAR_KG_PER_M;
  totals.steelKg += ringBeamSteel + columnSteel;
  const frame: MaterialsSection = {
    title: "Ring beam & columns",
    items: [
      { label: "Ring beam concrete (1:2:4)", quantity: r1(ringBeamVol), unit: "m³" },
      { label: "Columns (est.)", quantity: columnCount, unit: "no." },
      { label: "Column concrete (1:2:4)", quantity: r1(columnVol), unit: "m³" },
      {
        label: "→ Cement (beam + columns)",
        quantity: ringBeam.cementBags + columns.cementBags,
        unit: "bags (50 kg)",
      },
      { label: "Reinforcement steel", quantity: Math.ceil(ringBeamSteel + columnSteel), unit: "kg" },
    ],
  };

  // ---- Upper floor slabs ----
  const sections: MaterialsSection[] = [substructure, groundSlabSection, walls, frame];
  if (d.floors > 1) {
    const upperSlabVol = footprint * A.UPPER_SLAB_THICKNESS_M * (d.floors - 1);
    const upperSlab = addConcrete(upperSlabVol);
    const upperSteel = upperSlabVol * A.SLAB_REBAR_KG_PER_M3;
    totals.steelKg += upperSteel;
    sections.push({
      title: `Suspended slab${d.floors > 2 ? "s" : ""} (${d.floors - 1})`,
      items: [
        { label: "Slab concrete (1:2:4, 150 mm)", quantity: r1(upperSlabVol), unit: "m³" },
        { label: "→ Cement", quantity: upperSlab.cementBags, unit: "bags (50 kg)" },
        { label: "Reinforcement steel", quantity: Math.ceil(upperSteel), unit: "kg" },
        { label: "Formwork area", quantity: r1(footprint * (d.floors - 1)), unit: "m²" },
      ],
    });
  }

  // ---- Roof ----
  if (flatRoof) {
    const roofSlabVol = footprint * A.UPPER_SLAB_THICKNESS_M;
    const roofSlab = addConcrete(roofSlabVol);
    const roofSteel = roofSlabVol * A.SLAB_REBAR_KG_PER_M3;
    totals.steelKg += roofSteel;
    const screedVol = footprint * A.FLAT_ROOF_SCREED_THICKNESS_M;
    const screed = addMortar(screedVol, "1:3");
    sections.push({
      title: "Flat concrete roof",
      items: [
        { label: "Roof slab concrete (1:2:4, 150 mm)", quantity: r1(roofSlabVol), unit: "m³" },
        { label: "→ Cement", quantity: roofSlab.cementBags, unit: "bags (50 kg)" },
        { label: "Reinforcement steel", quantity: Math.ceil(roofSteel), unit: "kg" },
        { label: "Waterproof screed cement (1:3)", quantity: screed.bags, unit: "bags" },
        { label: "Waterproofing membrane", quantity: r1(footprint * 1.1), unit: "m²" },
      ],
    });
  } else {
    const roofArea = footprint * A.PITCH_AREA_FACTOR;
    const cover = roofArea * A.ROOF_COVER_WASTE;
    const timber = roofArea * A.ROOF_TIMBER_M_PER_M2;
    totals.roofCoverM2 += cover;
    totals.roofTimberM += timber;
    const coverLabel = d.roofType.includes("iron")
      ? "Iron sheets (incl. laps)"
      : "Roofing tiles (incl. waste)";
    sections.push({
      title: "Pitched roof",
      items: [
        { label: "Roof area (pitched)", quantity: r1(roofArea), unit: "m²" },
        { label: coverLabel, quantity: r1(cover), unit: "m²" },
        { label: "Roof timber (rafters, purlins, ties)", quantity: Math.ceil(timber), unit: "m" },
      ],
    });
  }

  // ---- Finishes ----
  const finishItems: QuantityItem[] = [];
  let paintableArea = 0;
  if (d.plasterBothSides) {
    const plasterArea = netWallArea * 2;
    const plasterVol = plasterArea * A.PLASTER_THICKNESS_M;
    const plaster = addMortar(plasterVol, "1:4");
    paintableArea = plasterArea;
    finishItems.push(
      { label: "Plaster area (both faces, 12 mm)", quantity: r1(plasterArea), unit: "m²" },
      { label: "→ Plaster cement (1:4)", quantity: plaster.bags, unit: "bags" },
      { label: "→ Plaster sand", quantity: r1(plaster.sand), unit: "m³" },
    );
  } else {
    paintableArea = netWallArea;
  }
  if (d.paint) {
    const litres = paintableArea * A.PAINT_L_PER_M2;
    totals.paintLitres += litres;
    finishItems.push({ label: "Paint (two coats)", quantity: Math.ceil(litres), unit: "litres" });
  }
  const floorArea = footprint * d.floors;
  if (d.floorFinish === "screed") {
    const screedVol = floorArea * A.SCREED_THICKNESS_M;
    const screed = addMortar(screedVol, "1:3");
    finishItems.push(
      { label: "Floor screed area (32 mm)", quantity: r1(floorArea), unit: "m²" },
      { label: "→ Screed cement (1:3)", quantity: screed.bags, unit: "bags" },
    );
  } else {
    finishItems.push(
      { label: "Ceramic tiles (incl. 5% waste)", quantity: r1(floorArea * 1.05), unit: "m²" },
      {
        label: "Tile adhesive",
        quantity: Math.ceil((floorArea * A.TILE_ADHESIVE_KG_PER_M2) / 25),
        unit: "bags (25 kg)",
      },
    );
  }
  finishItems.push(
    { label: "Doors (units + frames)", quantity: d.doorsCount, unit: "no." },
    { label: "Windows (units + frames)", quantity: d.windowsCount, unit: "no." },
  );
  sections.push({ title: "Finishes & openings", items: finishItems });

  // Round totals for presentation
  totals.sandM3 = r1(totals.sandM3);
  totals.ballastM3 = r1(totals.ballastM3);
  totals.steelKg = Math.ceil(totals.steelKg);
  totals.brcMeshM2 = r1(totals.brcMeshM2);
  totals.roofTimberM = Math.ceil(totals.roofTimberM);
  totals.roofCoverM2 = r1(totals.roofCoverM2);
  totals.paintLitres = Math.ceil(totals.paintLitres);

  // Machine-readable measures for the cost engine.
  const upperSlabVolTotal = d.floors > 1 ? footprint * A.UPPER_SLAB_THICKNESS_M * (d.floors - 1) : 0;
  const externalFaceArea = Math.max(externalGross - openings / 2, 0); // openings shared between faces
  const plasterExt = d.plasterBothSides ? externalFaceArea : 0;
  const plasterInt = d.plasterBothSides ? Math.max(netWallArea * 2 - externalFaceArea, 0) : 0;
  const paintableExt = externalFaceArea;
  const paintableInt = Math.max((d.plasterBothSides ? netWallArea * 2 : netWallArea) - externalFaceArea, 0);
  const measures: Measures = {
    footprintM2: footprint,
    perimeterM: perimeter,
    excavationM3: excavation,
    backfillM3: excavation * 0.5, // est.: half of excavated volume returned as backfill
    footingConcreteM3: footingVol,
    foundationWallM2: foundationWallArea,
    hardcoreM2: footprint,
    blindingM2: footprint,
    dpmM2: footprint * 1.1,
    groundSlabM3: groundSlabVol,
    suspendedSlabM3: upperSlabVolTotal + (flatRoof ? footprint * A.UPPER_SLAB_THICKNESS_M : 0),
    slabFormworkM2: footprint * (d.floors - 1) + (flatRoof ? footprint : 0),
    ringBeamM3: ringBeamVol,
    columnConcreteM3: columnVol,
    steelKg: totals.steelKg,
    wallNetM2: netWallArea,
    wallThicknessMm: d.wallThicknessMm,
    wallIsStone: d.wallType === "natural_stone",
    lintelM: (d.doorsCount * 0.9 + d.windowsCount * 1.2) * 1.3, // opening widths + bearing
    pitchedRoofM2: flatRoof ? 0 : footprint * A.PITCH_AREA_FACTOR,
    roofCoverM2: totals.roofCoverM2,
    flatRoofM3: flatRoof ? footprint * A.UPPER_SLAB_THICKNESS_M : 0,
    flatRoofWaterproofM2: flatRoof ? footprint * 1.1 : 0,
    plasterExtM2: plasterExt,
    plasterIntM2: plasterInt,
    paintExtM2: d.paint ? paintableExt : 0,
    paintIntM2: d.paint ? paintableInt : 0,
    screedM2: d.floorFinish === "screed" ? footprint * d.floors : 0,
    tilesM2: d.floorFinish === "ceramic_tiles" ? footprint * d.floors : 0,
    doorsNo: d.doorsCount,
    windowsM2: d.windowsCount * A.WINDOW_AREA_M2,
  };

  return { engineVersion: ENGINE_VERSION, sections, totals, measures, assumptions: A };
}
