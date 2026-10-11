---
id: cineloop-31
project: cineloop
source: "cineloop/reboot-findings.md §21b (Part 4)"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - web-app/references/react-client.md
  - mcp-ui/references/react-scaffolding.md
tags: [frontend, scaffold, builder-drift]
cluster: "4.2"
still_applies: yes
status: Resolved
resolved_by: "web-app/references/react-client.md § Never"
---

# Do not ship a web app on Vite's default port (5173); set strictPort

**What happened.** Reported by the user: the app was blank on `http://localhost:5173` while it worked on `http://127.0.0.1:5173`. The QA run had seen the 404, noted it and moved on because the `127.0.0.1` URL worked; the URL a person types is `localhost`. Cause: another project's Vite server was already bound to `[::1]:5173`; this one bound the IPv6 wildcard `*:5173`. Both binds succeed (no 'address in use'), then `localhost` resolves to `::1` first so the other project answers, while `127.0.0.1` reaches this one. Without `strictPort` Vite silently slides to 5174, making `allowed_origins` and `.env` wrong without any announcement.

**Expected.** Add to `react-client.md` beside `server.host`: do not leave `port` at Vite's default; pick a project port and set `strictPort: true` (example `server: { host: true, port: 5273, strictPort: true }`) so a conflict fails loudly. General QA lesson: test the URL a person would type.

**Repro.** Two Vite dev servers on one machine, one on 5173 bound to `[::1]`, one on the wildcard; open `http://localhost:5173`.

**Where in the skills.** `web-app/references/react-client.md` (config snippet); `mcp-ui/references/react-scaffolding.md` already has `strictPort: true` (builder drift).

**Checked at 1.6.0.** `web-app/references/react-client.md` lines 58-72 still use `port: parseInt(process.env.PORT || "5173", 10)` with no `strictPort`; `mcp-ui/references/react-scaffolding.md:234` has `strictPort: true`, so the two builders disagree.
