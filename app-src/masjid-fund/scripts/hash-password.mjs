#!/usr/bin/env node
/**
 * Generate the ADMIN_PASSWORD_HASH value for a deployment.
 *
 *   npm run admin:hash -- 'the password'
 *
 * Format must stay in step with verifyPassword() in src/lib/admin.ts:
 * scrypt$<salt base64>$<key base64>, 16-byte salt, 64-byte key.
 */
import { randomBytes, scryptSync } from "node:crypto";

const password = process.argv[2];
if (!password) {
  console.error("Usage: npm run admin:hash -- 'the password'");
  process.exit(1);
}

const salt = randomBytes(16);
const key = scryptSync(password, salt, 64);
console.log(`scrypt$${salt.toString("base64")}$${key.toString("base64")}`);
