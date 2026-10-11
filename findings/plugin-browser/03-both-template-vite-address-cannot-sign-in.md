---
id: plugin-browser-03
project: plugin-browser
source: "plugin-browser/FINDINGS.md § Plugin skills, item 1"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - build/templates/README.md
tags: [scaffold, frontend]
cluster: ""
still_applies: yes
status: Resolved
resolved_by: "build/templates/README.md § Files"
---
# `both` template: Vite prints an address whose sign-in can't work

**What happened.** After adding the MCP front door (`build/templates/both/`), `cd frontend && npm run dev` prints `Local: http://localhost:4444/`. Pressing Sign in there lands on Vite's own page: "The server is configured with a public base URL of /__/frontend/ - did you mean to visit /__/frontend/__/oauth/start?return_to=…". The web app finds the backend at its own origin, which is Vite there. Through the backend (`http://localhost:9991/__/frontend/web/`) it works.

**Expected.** `frontend/vite.config.ts` says the SPA reaches the backend via `VITE_REBOOT_URL` (see `web/.env.development`) and sets `envDir` to `web/`, but the template ships no `frontend/web/.env.development`, and `build/templates/README.md` says the `both` SPA needs none. Adding it with `VITE_REBOOT_URL=http://localhost:9991` (then restarting Vite, which doesn't reload env files) made both addresses sign in. A `.env.development` in `frontend/` is not read.

**Repro.** Copy `both`, run the backend and `npm run dev`, open the URL Vite prints, press Sign in.

**Where in the skills.** `build/templates/both/frontend/web/` (the missing file), `build/templates/README.md` ("`both/` adds"), the `run` skill's hand-off (which URL to give for a `both` app).

**Resolution (2026-10-10).** The `both` template ships `frontend/web/.env.development` with the backend's port (`copy.sh` writes it), so the address Vite prints can sign in; the templates' README row for the SPA entry says so.
