import { defineConfig } from "astro/config";
import react from "@astrojs/react";

// package.json pins "astro": "^7.3.0", "@astrojs/react": "^5.0.0"
export default defineConfig({
  site: "https://shop.example.com",
  output: "hybrid",
  integrations: [react()],
  experimental: {
    actions: true,
    serverIslands: true,
  },
  vite: {
    build: {
      rollupOptions: {
        output: { manualChunks: { vendor: ["react", "react-dom"] } },
      },
    },
  },
});
