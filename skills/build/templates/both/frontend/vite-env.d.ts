/// <reference types="vite/client" />

interface ImportMetaEnv {
  // The deployed backend, for a web app published on its own domain.
  readonly VITE_REBOOT_URL?: string;
  // The deployed web app, for an MCP UI's "Open in web app" link.
  readonly VITE_WEB_APP_URL?: string;
}
