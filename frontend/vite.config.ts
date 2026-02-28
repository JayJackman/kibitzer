/**
 * Vite configuration for the Bridge frontend.
 *
 * Three key things configured here:
 * 1. React plugin -- enables JSX/TSX support
 * 2. Tailwind CSS v4 plugin -- processes Tailwind classes in CSS
 * 3. Proxy -- forwards "/api" requests to the FastAPI backend
 *    so cookies work without cross-origin issues
 */
import path from "path";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      // Makes "@/foo" resolve to "src/foo" in imports.
      // Must match the "paths" config in tsconfig.json.
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    // Proxy API requests to the FastAPI backend during development.
    // When the browser requests "/api/auth/me" on port 5173, Vite
    // forwards it to "http://localhost:8000/api/auth/me".
    // This keeps everything same-origin so cookies work automatically.
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
