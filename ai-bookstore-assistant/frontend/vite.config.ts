import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The dev server runs on port 5173 and talks to the FastAPI backend on 8000
// (see src/api.ts). CORS is enabled on the backend, so no proxy is required.
export default defineConfig({
  plugins: [react()],
  server: { port: 5173 },
});
