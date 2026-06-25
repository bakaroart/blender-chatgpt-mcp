import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "node",
    testTimeout: 10000,
    exclude: ["node_modules/**", "dist/**"],
    restoreMocks: true,
    coverage: {
      reporter: ["text", "lcov"]
    }
  }
});
