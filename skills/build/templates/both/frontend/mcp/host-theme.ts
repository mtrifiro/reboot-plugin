import { useEffect } from "react";
import { applyDocumentTheme } from "@modelcontextprotocol/ext-apps";
import { useMcpApp } from "@reboot-dev/reboot-react";

type Theme = "light" | "dark";

// The host owns light and dark: follow its theme now and whenever it
// changes. `applyDocumentTheme` sets data-theme and color-scheme on
// <html>, which `styles.css` reads, as the web app's toggle does.
// Call it once, in each UI's top component (inside the provider).
export function useHostTheme(): void {
  const app = useMcpApp(); // `null` outside a host and on early renders
  useEffect(() => {
    if (!app) return;
    const theme: Theme | undefined = app.getHostContext()?.theme;
    if (theme) applyDocumentTheme(theme);
    const onChange = (context: { theme?: Theme }) => {
      if (context.theme) applyDocumentTheme(context.theme);
    };
    // A listener, not `onhostcontextchanged`, so it composes with others.
    app.addEventListener("hostcontextchanged", onChange);
    return () => app.removeEventListener("hostcontextchanged", onChange);
  }, [app]);
}
