import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "path";

// https://vitejs.dev/config/
export default defineConfig({
  base: "./",
  plugins: [react()],
  build: {
    // Output directly into the extension/sidebar folder so
    // manifest.json's `side_panel.default_path` points to the built file.
    outDir: "dist",
    rollupOptions: {
      input: {
        sidebar: resolve(__dirname, "index.html"),
      },
    },
  },
});
