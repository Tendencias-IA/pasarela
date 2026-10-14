/// <reference types="vitest/config" />
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// La API corre en 5000 (flask/gunicorn). dev y preview reenvían /api y /health para
// mantener un solo origen (cookie SameSite=Lax, sin CORS). Ver .claude/rules/webapp.md.
const apiProxy = {
  "/api": { target: "http://127.0.0.1:5000", changeOrigin: false },
  "/health": { target: "http://127.0.0.1:5000", changeOrigin: false },
};

export default defineConfig({
  plugins: [react()],
  server: { host: "127.0.0.1", port: 5173, strictPort: true, proxy: apiProxy },
  preview: { host: "127.0.0.1", port: 4173, strictPort: true, proxy: apiProxy },
  build: {
    outDir: "dist",
    sourcemap: false,
    // Ionic core pesa ~1,2 MB minificado (266 kB gzip); se separa en su propio chunk y se
    // sube el umbral de aviso solo para él (ADR-0007).
    chunkSizeWarningLimit: 1500,
    rolldownOptions: {
      output: {
        manualChunks: (id: string) =>
          id.includes("node_modules/@ionic") || id.includes("node_modules/ionicons")
            ? "ionic"
            : id.includes("node_modules/react")
              ? "react"
              : undefined,
      },
    },
  },
  test: {
    environment: "jsdom",
    globals: false,
    setupFiles: ["./src/test/setup.ts"],
    include: ["src/**/*.test.{ts,tsx}"],
    coverage: {
      provider: "v8",
      reporter: ["text", "lcov"],
      include: ["src/**/*.{ts,tsx}"],
      exclude: [
        "src/**/*.test.{ts,tsx}",
        "src/test/**",
        "src/main.tsx",
        "src/shared/api/types.gen.ts",
      ],
    },
  },
});
