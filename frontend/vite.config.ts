import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const apiBase = process.env.VITE_API_BASE || "http://localhost:8000";
const wsBase = apiBase.replace(/^http/, "ws");

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    proxy: {
      "/api": { target: apiBase, changeOrigin: true },
      "/ws": { target: wsBase, ws: true, changeOrigin: true },
    },
  },
});
