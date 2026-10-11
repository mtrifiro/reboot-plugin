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

// In development the SPA is served by Vite and the backend listens on
// :9991, so name the backend explicitly (`web/.env.development`). The
// fallback serves a build the backend hosts on its own origin.
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
