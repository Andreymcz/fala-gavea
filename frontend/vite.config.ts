import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  build: { outDir: "../static", emptyOutDir: true },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
  },
  server: {
    port: 5173,
    proxy: Object.fromEntries(
      ["/auth", "/reports", "/report_types", "/forwardings", "/nl", "/admin"].map((p) => [
        p,
        { target: "http://localhost:8000", changeOrigin: true },
      ]),
    ),
  },
  resolve: { alias: { "@": path.resolve(__dirname, "./src") } },
});
