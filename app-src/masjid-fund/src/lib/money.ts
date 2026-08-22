/**
 * Money helpers. Amounts are integer minor units (cents) everywhere in the
 * app; they are only turned into decimals at the display edge.
 */

/**
 * The accounting currency. Project budgets and every published total are in
 * USD; a donation made in another currency is converted once, at the moment it
 * is created, and both figures are kept.
 */
export const BASE_CURRENCY = "USD";
export const DEFAULT_CURRENCY = BASE_CURRENCY;

export const CURRENCIES = ["USD", "KES"] as const;
export type Currency = (typeof CURRENCIES)[number];

/** $1 minimum keeps card fees from exceeding the gift; $50,000 ceiling routes large gifts to a human. */
export const MIN_DONATION_CENTS = 100;
export const MAX_DONATION_CENTS = 5_000_000;

/**
 * USD → KES rate, set in the environment and reviewed by hand.
 *
 * Deliberately not a live feed: a rate that moves between the page load and the
 * charge makes receipts disagree with the ledger, and an outage in a rate
 * service would stop donations. A stale rate is a small, visible accounting
 * discrepancy; a broken donate button is a lost gift.
 */
export function usdToKesRate(): number {
  const configured = Number(process.env.USD_KES_RATE);
  return Number.isFinite(configured) && configured > 0 ? configured : 129;
}

/** Smallest step a currency can actually be charged in, in minor units. */
export function minorUnitStep(currency: Currency): number {
  // M-Pesa moves whole shillings only, so KES amounts are always a round 100.
  return currency === "KES" ? 100 : 1;
}

/** Convert a base-currency (USD) amount into what the donor will be charged. */
export function fromBase(baseCents: number, currency: Currency): number {
  if (currency === BASE_CURRENCY) return baseCents;
  const converted = baseCents * usdToKesRate();
  const step = minorUnitStep(currency);
  return Math.round(converted / step) * step;
}

/** Convert a charged amount back into the base currency for the ledger. */
export function toBase(cents: number, currency: Currency): number {
  if (currency === BASE_CURRENCY) return cents;
  return Math.round(cents / usdToKesRate());
}

export function isCurrency(value: unknown): value is Currency {
  return typeof value === "string" && (CURRENCIES as readonly string[]).includes(value);
}

/** bigint columns arrive as strings from node-postgres — normalize on read. */
export function toCents(value: unknown): number {
  if (typeof value === "number") return Math.round(value);
  if (typeof value === "bigint") return Number(value);
  const n = Number(value ?? 0);
  return Number.isFinite(n) ? Math.round(n) : 0;
}

export function formatMoney(cents: number, currency = DEFAULT_CURRENCY): string {
  const whole = cents % 100 === 0;
  // Kenyan shillings read as "Ksh" to a Kenyan donor and as "KES" to everyone
  // else; the local form is the right one on a site raising money in Kenya.
  const locale = currency === "KES" ? "en-KE" : "en-US";
  return new Intl.NumberFormat(locale, {
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
