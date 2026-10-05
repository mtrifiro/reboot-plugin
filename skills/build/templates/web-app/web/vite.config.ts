import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  // Two copies of `react` or `zod` — one from the app, one pulled
  // through the Reboot packages — break hooks and schema identity
  // checks at runtime.
  resolve: { dedupe: ["react", "react-dom", "zod"] },
  server: {
    // Listen on every interface. Vite's default is `localhost`,
    // which on modern Node resolves to IPv6 `[::1]` only; a
    // forwarded port (Codespaces, VS Code remote, a dev VM, a
    // tunnel) connects over IPv4 `127.0.0.1` and gets connection
    // refused, so the page is unreachable from the browser even
    // though the dev server is healthy and logs no error.
    host: true,
    // A port of this project's own, not Vite's default 5173, which
    // another project's dev server may already hold on `[::1]`.
    // Change it if another project on this machine uses it.
    port: 5273,
    // Fail loudly if the port is taken instead of silently sliding
    // to the next one.
    strictPort: true,
  },
});
