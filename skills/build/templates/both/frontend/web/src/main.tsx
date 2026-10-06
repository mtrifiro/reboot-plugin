import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { RebootClientProvider } from "@reboot-dev/reboot-react";
import { App } from "./App";
// Reboot's typefaces, bundled so the app needs no font CDN (styles.css
// names them in --font-display, --font-text and --font-mono).
import "@fontsource-variable/space-grotesk";
import "@fontsource-variable/dm-sans";
import "@fontsource/dm-mono/400.css";
import "@fontsource/dm-mono/500.css";
import "./styles.css";
import { applySavedTheme } from "./theme";

// The backend serves this SPA at `/__/frontend/web/` (Vite proxied in
// dev, `dist/web/` otherwise), so its own origin is the backend. A
// build published on its own domain sets `VITE_REBOOT_URL` in
// `web/.env.production` (the `deploy` skill).
const REBOOT_URL =
  (import.meta.env.VITE_REBOOT_URL as string | undefined) ??
  window.location.origin;

applySavedTheme();

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <RebootClientProvider url={REBOOT_URL}>
      <App />
    </RebootClientProvider>
  </StrictMode>
);
