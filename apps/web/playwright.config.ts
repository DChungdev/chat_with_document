import { defineConfig } from "@playwright/test";

// E2E chạy trên chế độ local (devserver: API + worker + giao diện đã build, KHÔNG cần Docker).
// Cần build giao diện trước: `pnpm build` (script `pnpm e2e` làm sẵn).
const PORT = 8765;
const python = process.platform === "win32" ? ".venv\\Scripts\\python.exe" : ".venv/bin/python";

export default defineConfig({
  testDir: "./e2e",
  timeout: 45_000,
  expect: { timeout: 10_000 },
  fullyParallel: false, // dữ liệu nằm trong bộ nhớ một tiến trình; mỗi test dùng người dùng riêng nên vẫn cô lập
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["github"], ["html", { open: "never" }]] : [["list"]],
  use: {
    baseURL: `http://127.0.0.1:${PORT}`,
    // Máy dev dùng Edge có sẵn (không tải trình duyệt); CI cài chromium (`playwright install chromium`).
    channel: process.env.E2E_CHANNEL ?? (process.env.CI ? undefined : "msedge"),
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    locale: "vi-VN",
  },
  webServer: {
    command: `${python} -m docchat_api.devserver --port ${PORT}`,
    cwd: "../..",
    url: `http://127.0.0.1:${PORT}/health`,
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
    env: { ENVIRONMENT: "dev", PYTHONUTF8: "1", LOG_LEVEL: "WARNING", FAKE_LLM_DELAY: "0.12" },
  },
});
