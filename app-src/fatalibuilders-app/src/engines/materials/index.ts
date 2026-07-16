/**
 * Materials quantities engine — Release 1.0, residential scope.
 *
 * Every exported function must be covered by unit tests validated against
 * worked examples approved by the owner-engineer (CORE-5.0 acceptance).
 * The functions below are the first verified building blocks; the full
 * residential rule-set lands in CORE-5.0.
 */

export const ENGINE_VERSION = "0.1.0";

/** Volume of a rectangular concrete element (m³). */
export function concreteVolume(lengthM: number, widthM: number, depthM: number): number {
  assertPositive({ lengthM, widthM, depthM });
  return round3(lengthM * widthM * depthM);
}

/**
 * Cement, sand and ballast for a concrete volume using a nominal mix ratio
 * (e.g. 1:2:4 for C20/25-class site mixes). Dry-volume factor 1.54 per
 * standard practice; cement bag = 50 kg = 0.0347 m³.
 * Baseline convention pending owner-engineer validation in CORE-5.0.
 */
export function concreteMaterials(
  volumeM3: number,
  mix: { cement: number; sand: number; ballast: number } = { cement: 1, sand: 2, ballast: 4 },
): { cementBags: number; sandM3: number; ballastM3: number } {
  assertPositive({ volumeM3 });
  const totalParts = mix.cement + mix.sand + mix.ballast;
  const dryVolume = volumeM3 * 1.54;
  const cementM3 = (dryVolume * mix.cement) / totalParts;
  return {
    cementBags: Math.ceil(cementM3 / 0.0347),
    sandM3: round3((dryVolume * mix.sand) / totalParts),
    ballastM3: round3((dryVolume * mix.ballast) / totalParts),
  };
}

/**
 * Masonry units for a wall area, with an allowance for mortar joints and
 * waste. Default: standard 400×200 mm face block, 12.5 units/m² gross,
 * 5% waste. Baseline convention pending owner-engineer validation.
 */
export function wallBlocks(
  wallAreaM2: number,
  opts: { unitsPerM2?: number; wastePct?: number } = {},
): number {
  assertPositive({ wallAreaM2 });
  const { unitsPerM2 = 12.5, wastePct = 5 } = opts;
  return Math.ceil(wallAreaM2 * unitsPerM2 * (1 + wastePct / 100));
}

function assertPositive(values: Record<string, number>): void {
  for (const [name, value] of Object.entries(values)) {
    if (!Number.isFinite(value) || value <= 0) {
      throw new RangeError(`${name} must be a positive number, got ${value}`);
    }
  }
}

function round3(n: number): number {
  return Math.round(n * 1000) / 1000;
}
