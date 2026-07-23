import path from "node:path";
import { defineConfig } from "vitest/config";

export default defineConfig({
  resolve: {
    alias: { "@": path.resolve(__dirname, "src") },
  },
  test: {
    include: ["src/**/*.test.ts"],
    environment: "node",
    // Each test gets a fresh embedded PGlite database and argon2 hashing is
    // deliberately slow — allow generous time per test.
    testTimeout: 30000,
  },
});
