import path from "node:path";
import react from "@vitejs/plugin-react-swc";
import { defineConfig } from "vite";

// https://vitejs.dev/config/
export default defineConfig({
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  build: {
    rollupOptions: {
      input: {
        index: path.resolve(__dirname, "index.html"),
        registrationForm: path.resolve(__dirname, "registration-form.html"),
        dashboard: path.resolve(__dirname, "gowithDaddy_dashboard.html"),
        addPackage: path.resolve(__dirname, "addPackage.html"),
      },
    },
  },
  plugins: [react()],
});
