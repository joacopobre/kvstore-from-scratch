   import { defineConfig } from "vite";

   export default defineConfig({
     root: "site",
     server: { proxy: { "/api": "http://localhost:3000" } },
     build: { outDir: "../dist", emptyOutDir: true },
   });