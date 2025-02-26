import react from "@vitejs/plugin-react-swc";
import { defineConfig } from "vitest/config";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 2825,
    // WSL2 doesn't propogate file changes, so we need to poll to enable HMR
    watch: {
      usePolling: true,
      interval: 500,
    },
  },
  envDir: "./config/",
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: "./src/setupTests.ts",
  },
});
