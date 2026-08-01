import { z } from "zod";
import { MAX_DONATION_CENTS, MIN_DONATION_CENTS, formatMoney } from "./money";

/**
 * Donation domain rules — shared by the donate form (client) and the API
 * route (server). The server always re-validates; the client uses the same
 * schema so the messages match.
 */

export const FREQUENCIES = ["one_time", "monthly"] as const;
export type Frequency = (typeof FREQUENCIES)[number];

export const INTENTS = ["sadaqah_jariyah", "general_sadaqah", "zakat"] as const;
export type Intent = (typeof INTENTS)[number];

export const INTENT_LABELS: Record<Intent, string> = {
  sadaqah_jariyah: "Sadaqah Jariyah",
  general_sadaqah: "General Sadaqah",
  zakat: "Zakat",
};

export const INTENT_NOTES: Record<Intent, string> = {
  sadaqah_jariyah:
    "An ongoing charity — the reward continues for as long as the masjid is used for prayer.",
  general_sadaqah: "Voluntary charity, applied to whichever stage of the build needs it next.",
  zakat:
    "Most scholars hold that masjid construction is not a valid category for zakat. Zakat given here is held separately and passed to eligible recipients, never to building costs.",
};

export const STATUSES = ["pending", "completed", "failed", "refunded"] as const;
export type DonationStatus = (typeof STATUSES)[number];

/** Preset amounts (in cents) offered on the donate form. */
export const PRESET_AMOUNTS_CENTS = [2500, 5000, 10000, 25000, 50000, 100000];

export const donationInputSchema = z.object({
  amountCents: z
    .number({ invalid_type_error: "Enter a donation amount" })
    .int("Enter a whole amount in cents")
    .min(MIN_DONATION_CENTS, `The smallest donation we can process is ${formatMoney(MIN_DONATION_CENTS)}`)
    .max(
      MAX_DONATION_CENTS,
      `For gifts above ${formatMoney(MAX_DONATION_CENTS)}, please contact us so we can arrange a transfer`,
    ),
  projectSlug: z.string().trim().min(1).max(120).nullable().optional(),
  frequency: z.enum(FREQUENCIES).default("one_time"),
  intent: z.enum(INTENTS).default("sadaqah_jariyah"),
  donorName: z.string().trim().max(120).optional().or(z.literal("")),
  donorEmail: z.string().trim().toLowerCase().email("Enter a valid email so we can send your receipt"),
  anonymous: z.boolean().default(false),
  dedication: z.string().trim().max(160).optional().or(z.literal("")),
  message: z.string().trim().max(500).optional().or(z.literal("")),
});

export type DonationInput = z.infer<typeof donationInputSchema>;

export class DonationError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

/** Parse untrusted input, throwing a DonationError carrying the first message. */
export function parseDonationInput(raw: unknown): DonationInput {
  const result = donationInputSchema.safeParse(raw);
  if (!result.success) {
    throw new DonationError(result.error.issues[0]?.message ?? "Invalid donation details", 400);
  }
  return result.data;
}

/** Public display name for a donation in the recent-gifts feed. */
export function displayDonorName(donation: {
  anonymous: boolean;
  donorName: string | null;
}): string {
  if (donation.anonymous || !donation.donorName) return "Anonymous";
  return donation.donorName;
}
