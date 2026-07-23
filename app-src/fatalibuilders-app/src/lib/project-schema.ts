import { z } from "zod";

/**
 * The unified project-data input model (architecture §1.1): the user enters
 * this ONCE; every output (quantities, costs, labor, drawings, structural,
 * geotech) derives from it. Residential scope for Release 1.0.
 * Stored as JSONB; validated here at every boundary. schemaVersion guards
 * future migrations when R2/R3 add fields.
 */

export const CODE_PROFILE_IDS = ["eurocode", "bs", "kebs"] as const;

export const WALL_TYPES = {
  concrete_block: "Concrete blocks",
  brick: "Bricks",
  natural_stone: "Natural stone (machine-cut)",
} as const;

export const ROOF_TYPES = {
  gable_iron_sheets: "Gable roof — iron sheets (mabati)",
  hip_iron_sheets: "Hip roof — iron sheets (mabati)",
  gable_tiles: "Gable roof — tiles",
  hip_tiles: "Hip roof — tiles",
  flat_concrete: "Flat concrete roof",
} as const;

export const FLOOR_FINISHES = {
  screed: "Cement screed",
  ceramic_tiles: "Ceramic tiles",
} as const;

export const SOIL_TYPES = {
  unknown: "Not known yet",
  clay: "Clay",
  black_cotton: "Black cotton soil",
  silt: "Silt",
  sand: "Sand",
  gravel: "Gravel",
  rock: "Rock",
} as const;

export const projectDataSchema = z.object({
  schemaVersion: z.literal(1).default(1),
  codeProfile: z.enum(CODE_PROFILE_IDS).default("eurocode"),
  country: z.string().trim().min(2, "Enter the project country").default("Kenya"),
  floors: z.coerce.number().int().min(1).max(4).default(1),
  footprintLengthM: z.coerce
    .number({ message: "Enter the building length in metres" })
    .positive("Length must be greater than zero")
    .max(100, "For buildings over 100 m contact us"),
  footprintWidthM: z.coerce
    .number({ message: "Enter the building width in metres" })
    .positive("Width must be greater than zero")
    .max(100, "For buildings over 100 m contact us"),
  floorHeightM: z.coerce.number().min(2.2, "Minimum floor height is 2.2 m").max(4.5).default(2.8),
  wallType: z.enum(Object.keys(WALL_TYPES) as [keyof typeof WALL_TYPES]).default("concrete_block"),
  wallThicknessMm: z.coerce
    .number()
    .int()
    .refine((v) => [150, 200, 230].includes(v), "Choose 150, 200 or 230 mm")
    .default(200),
  roofType: z
    .enum(Object.keys(ROOF_TYPES) as [keyof typeof ROOF_TYPES])
    .default("gable_iron_sheets"),
  doorsCount: z.coerce.number().int().min(0).max(100).default(6),
  windowsCount: z.coerce.number().int().min(0).max(200).default(8),
  plasterBothSides: z.coerce.boolean().default(true),
  paint: z.coerce.boolean().default(true),
  floorFinish: z
    .enum(Object.keys(FLOOR_FINISHES) as [keyof typeof FLOOR_FINISHES])
    .default("screed"),
  soilType: z.enum(Object.keys(SOIL_TYPES) as [keyof typeof SOIL_TYPES]).default("unknown"),
});

/** Complete, calculation-ready project data (required at "Finish"). */
export type ProjectData = z.infer<typeof projectDataSchema>;

/** Partial data while the wizard is in progress (drafts autosave any subset). */
export const projectDraftSchema = projectDataSchema.partial();
export type ProjectDraft = z.infer<typeof projectDraftSchema>;

export interface ProjectRecord {
  id: string;
  name: string;
  status: "draft" | "complete";
  data: ProjectDraft;
  createdAt: string;
  updatedAt: string;
}
