import { z } from "zod";

/**
 * Application domain rules — shared by the public form (client) and the intake
 * route (server), so the two cannot drift apart.
 *
 * Nothing here may import the database or any server-only module: this file is
 * bundled into the browser. Data access lives in applications.ts.
 */

export const APPLICATION_STATUSES = [
  "submitted",
  "in_review",
  "needs_info",
  "approved",
  "rejected",
] as const;
export type ApplicationStatus = (typeof APPLICATION_STATUSES)[number];

export const STATUS_LABELS: Record<ApplicationStatus, string> = {
  submitted: "Received",
  in_review: "Under review",
  needs_info: "More information needed",
  approved: "Approved",
  rejected: "Not accepted",
};

export const LAND_OWNERSHIP = [
  "waqf_trust",
  "community_trust",
  "registered_society",
  "individual",
  "leasehold",
  "other",
] as const;
export type LandOwnership = (typeof LAND_OWNERSHIP)[number];

export const LAND_OWNERSHIP_LABELS: Record<LandOwnership, string> = {
  waqf_trust: "Waqf trust",
  community_trust: "Community trust",
  registered_society: "Registered society or association",
  individual: "An individual",
  leasehold: "Leasehold",
  other: "Something else",
};

/** Applications may be costed in either currency; staff set the USD goal at publication. */
export const APPLICATION_CURRENCIES = ["USD", "KES"] as const;

export class ApplicationError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

export const applicationInputSchema = z.object({
  masjidName: z.string().trim().min(2, "What will the masjid be called?").max(120),
  city: z.string().trim().min(1, "Which town or city?").max(80),
  country: z.string().trim().min(1, "Which country?").max(80),
  locationNote: z.string().trim().max(300).optional().or(z.literal("")),
  congregationNow: z.number().int().min(0).max(100000),
  capacityPlanned: z
    .number()
    .int()
    .min(10, "How many worshippers will the new masjid hold?")
    .max(100000),
  estimatedCostCents: z.number().int().min(100000, "Enter the estimated total cost of the build"),
  alreadyRaisedCents: z.number().int().min(0),
  currency: z.enum(APPLICATION_CURRENCIES),
  landTitleNumber: z.string().trim().min(2, "Enter the title deed number").max(80),
  landOwnership: z.enum(LAND_OWNERSHIP),
  titledToTrust: z.boolean(),
  trustName: z.string().trim().max(160).optional().or(z.literal("")),
  trustRegistration: z.string().trim().max(80).optional().or(z.literal("")),
  contactName: z.string().trim().min(2, "Who should we speak to?").max(120),
  contactRole: z.string().trim().min(2, "What is their role on the committee?").max(120),
  contactEmail: z.string().trim().toLowerCase().email("Enter a valid email address"),
  contactPhone: z.string().trim().min(6, "Enter a phone number we can reach you on").max(40),
  story: z
    .string()
    .trim()
    .min(80, "Tell us about the community and why the masjid is needed — a short paragraph at least")
    .max(4000),
  consentTruthful: z
    .boolean()
    .refine((v) => v, "Please confirm the information you have given is true"),
  consentPublish: z
    .boolean()
    .refine((v) => v, "We need permission to publish the project details if it is approved"),
});

export type ApplicationInput = z.infer<typeof applicationInputSchema>;

export function parseApplicationInput(raw: unknown): ApplicationInput {
  const result = applicationInputSchema.safeParse(raw);
  if (!result.success) {
    throw new ApplicationError(
      result.error.issues[0]?.message ?? "Check the form and try again",
      400,
    );
  }
  return result.data;
}
