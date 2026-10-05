import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { RebootClientProvider } from "@reboot-dev/reboot-react";
import { App } from "./App";
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
