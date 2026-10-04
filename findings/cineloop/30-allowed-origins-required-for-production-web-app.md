---
id: cineloop-30
project: cineloop
source: "cineloop/reboot-findings.md §21 (Part 4)"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - web-app/SKILL.md
  - web-app/references/react-client.md
  - deploy/SKILL.md
tags: [auth, negative-space, frontend]
cluster: "4.2"
still_applies: yes
status: Open
resolved_by: ""
---

# allowed_origins=[...] is required for production (not in web-app skill)

**What happened.** Starting the app printed that `Application(oauth=...)` is running without `allowed_origins=[...]`; works under `rbt dev run` but the same configuration will fail to deploy to production. Good warning (fires when the code is in your head; the same channel carries the 'unauthorized method' TODO list). Documentation gap: neither `web-app/SKILL.md` nor `react-client.md` mentions `allowed_origins` at all, though every web app hits it (Vite on 5173, backend on 9991 is cross-origin by construction).

**Expected.** Add to `web-app/SKILL.md`'s auth section: `allowed_origins=[...]` is required for production; a standalone SPA is cross-origin from its backend by construction; `rbt dev run` allows `http://localhost(:*)` implicitly so it is invisible in development and then blocks the first deploy; set it when setting `oauth=` (example `allowed_origins=["https://app.example.com"]`). Also read `rbt dev run` startup output on purpose.

**Repro.** Run a web app with `oauth=` and no `allowed_origins`; read startup output.

**Where in the skills.** `web-app/SKILL.md` auth section; `deploy/SKILL.md` already covers it at deploy time.

**Checked at 1.6.0.** `web-app/SKILL.md` and `web-app/references/react-client.md` still do not mention `allowed_origins`. It is covered in `deploy/SKILL.md` (lines 20, 92, 110, 254) and in `upgrade/migrations/1.3.0/oauth-allowed-origins.md`, so the gap is only at build time.
