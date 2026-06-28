import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev server proxies the API to FastAPI so `npm run dev` works standalone.
// `npm run build` emits ../web-dist, which server.py serves in production.
export default defineConfig({
  plugins: [react()],
  build: { outDir: "../web-dist", emptyOutDir: true },
  server: {
    proxy: { "/api": "http://127.0.0.1:8000" },
  },
});
