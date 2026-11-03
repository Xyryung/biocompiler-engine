import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests", timeout: 60_000, workers: 1,
  use: { baseURL: "http://127.0.0.1:3000", viewport: { width: 1920, height: 1080 }, trace: "retain-on-failure" },
  webServer: [
    { command: "uv run uvicorn biocompiler.api.main:app --host 127.0.0.1 --port 8000", cwd: "../..", url: "http://127.0.0.1:8000/health", reuseExistingServer: !process.env.CI, timeout: 60_000, env: { BIOCOMPILER_PROVIDER: "mock", BIOCOMPILER_SIMULATOR: "local", PROTEIN_ENDPOINT: "" } },
    { command: "npm run start", url: "http://127.0.0.1:3000", reuseExistingServer: !process.env.CI, timeout: 60_000 },
  ],
});
