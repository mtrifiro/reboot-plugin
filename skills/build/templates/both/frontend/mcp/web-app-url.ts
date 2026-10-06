// Where "Open in web app" goes from an MCP UI
// (`mcp-ui/references/pop-out-to-web-app.md`). In dev the backend serves
// the web app at `/__/frontend/web/` on the same origin as this UI. In
// production the web app lives on its own domain (the `deploy` skill), so
// `VITE_WEB_APP_URL` in `web/.env.production` names it; the MCP builds
// read that file too (`envDir` in `vite.config.ts`).
const BASE =
  import.meta.env.VITE_WEB_APP_URL ??
  `${window.location.origin}/__/frontend/web/`;

export function webAppUrl(path = ""): string {
  return new URL(path.replace(/^\//, ""), BASE.endsWith("/") ? BASE : `${BASE}/`).toString();
}
