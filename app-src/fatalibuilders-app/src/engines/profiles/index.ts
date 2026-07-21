/**
 * Code profiles — every calculation and generated document is traceable to
 * the design-code system the user selected for their project.
 * See memory: FatalibuildersConstructionApp_architecture.md §1.3.
 */
export const CODE_PROFILES = {
  eurocode: {
    id: "eurocode",
    label: "Eurocodes (EN 1990–1999)",
    description:
      "Modern European structural design codes. Recommended default; widely adopted including in Kenya.",
  },
  bs: {
    id: "bs",
    label: "British Standards (BS)",
    description:
      "Legacy British codes (BS 8110, 5950, 6399, 8004, 5628). Still widely used on older projects.",
  },
  kebs: {
    id: "kebs",
    label: "Kenya (KEBS KS + Eurocode/BS practice)",
    description:
      "Kenyan practice: Eurocodes and BS as commonly adopted, with KEBS KS adaptations.",
  },
} as const;

export type CodeProfileId = keyof typeof CODE_PROFILES;

/** Stamp rendered onto every result and exported document. */
export function profileStamp(profile: CodeProfileId, engineVersion: string): string {
  return `${CODE_PROFILES[profile].label} · engine v${engineVersion}`;
}
