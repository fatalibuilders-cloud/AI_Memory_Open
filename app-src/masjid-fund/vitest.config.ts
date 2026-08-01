import path from "node:path";
import { defineConfig } from "vitest/config";

export default defineConfig({
  resolve: {
    alias: { "@": path.resolve(__dirname, "src") },
  },
  test: {
    include: ["src/**/*.test.ts"],
    environment: "node",
    // Each database-backed test boots a fresh in-memory PGlite instance,
    // which takes a couple of seconds on a cold start.
    testTimeout: 30_000,
  },
});
