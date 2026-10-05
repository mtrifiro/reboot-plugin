import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { RebootClientProvider } from "@reboot-dev/reboot-react";
import { App } from "./App";
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
