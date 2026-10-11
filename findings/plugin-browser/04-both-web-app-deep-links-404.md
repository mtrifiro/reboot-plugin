---
id: plugin-browser-04
project: plugin-browser
source: "plugin-browser/FINDINGS.md § Plugin skills, item 2"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - build/SKILL.md
  - web-app/references/react-client.md
tags: [negative-space, frontend]
cluster: ""
still_applies: yes
status: Resolved
resolved_by: "build/SKILL.md § Update Flow"
---
# A `both` web app can't use path routes: deep links 404 under `/__/frontend/web/`

**What happened.** Moving the web app from `web/` (its own origin, `/kind/finding` routes) into `frontend/web/` serves it under `/__/frontend/web/`, where neither Vite nor the backend falls back to `index.html` for a deeper path. Reloading or deep-linking `/__/frontend/web/kind/finding`, or an MCP view's "Open in web app" link to one, fails. Switching the router to hash routes (`/__/frontend/web/#/kind/finding`) works under both.

**Expected.** The build skill's "Adding the other front door" to say that the SPA's routes move under a base path, and what routing survives it.

**Repro.** A `both` app with a path-routed SPA; open `/__/frontend/web/<route>` directly.

**Where in the skills.** `build/SKILL.md` § Update Flow, "Adding the other front door"; `web-app/references/react-client.md`.

**Resolution (2026-10-10).** The build skill's "Adding the other front door" says the SPA now serves under `/__/frontend/web/`, where deep links to path routes 404, and to switch to hash routes.
