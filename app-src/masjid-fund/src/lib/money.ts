/**
 * Money helpers. Amounts are integer minor units (cents) everywhere in the
 * app; they are only turned into decimals at the display edge.
 */

export const DEFAULT_CURRENCY = "USD";

/** $1 minimum keeps card fees from exceeding the gift; $50,000 ceiling routes large gifts to a human. */
export const MIN_DONATION_CENTS = 100;
export const MAX_DONATION_CENTS = 5_000_000;

/** bigint columns arrive as strings from node-postgres — normalize on read. */
export function toCents(value: unknown): number {
  if (typeof value === "number") return Math.round(value);
  if (typeof value === "bigint") return Number(value);
  const n = Number(value ?? 0);
  return Number.isFinite(n) ? Math.round(n) : 0;
}

export function formatMoney(cents: number, currency = DEFAULT_CURRENCY): string {
  const whole = cents % 100 === 0;
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: whole ? 0 : 2,
    maximumFractionDigits: whole ? 0 : 2,
  }).format(cents / 100);
}

/** Short form for headline figures: $84K, $1.2M. */
export function formatMoneyCompact(cents: number, currency = DEFAULT_CURRENCY): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    notation: "compact",
    maximumFractionDigits: 1,
    trailingZeroDisplay: "stripIfInteger",
  }).format(cents / 100);
}

/**
 * Parse donor-typed input ("25", "$1,250.50", " 40 ") into cents.
 * Returns null for anything that is not a usable amount.
 */
export function parseAmountToCents(input: string): number | null {
  const cleaned = input.replace(/[\s,$]/g, "");
  if (!/^\d+(\.\d{1,2})?$/.test(cleaned)) return null;
  const cents = Math.round(Number(cleaned) * 100);
  return Number.isFinite(cents) ? cents : null;
}

/** Funding progress, clamped to 0–100 so an over-funded project never breaks the bar. */
export function progressPercent(raisedCents: number, goalCents: number): number {
  if (goalCents <= 0) return 0;
  return Math.min(100, Math.max(0, Math.round((raisedCents / goalCents) * 100)));
}

/** How many units of a costed item a gift covers (e.g. 5 bags of cement). */
export function unitsCovered(amountCents: number, unitCostCents: number): number {
  if (unitCostCents <= 0) return 0;
  return Math.floor(amountCents / unitCostCents);
}
