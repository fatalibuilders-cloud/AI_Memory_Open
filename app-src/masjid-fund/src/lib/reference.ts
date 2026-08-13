import { randomBytes } from "crypto";

// Crockford-style alphabet: no I, L, O or U, so references survive being
// read down a phone line or copied off a paper receipt.
const ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ";

/** Donor-facing donation reference, e.g. MF-7K2QX9T4. */
export function newDonationReference(): string {
  const bytes = randomBytes(8);
  let out = "";
  for (const byte of bytes) out += ALPHABET[byte % ALPHABET.length];
  return `MF-${out}`;
}

/**
 * Secret that lets a donor manage a monthly gift straight from their receipt,
 * with no account to create. It is a bearer credential, so it is long enough
 * that guessing is hopeless — unlike the short human-readable reference.
 */
export function newManageToken(): string {
  return randomBytes(32).toString("base64url");
}
