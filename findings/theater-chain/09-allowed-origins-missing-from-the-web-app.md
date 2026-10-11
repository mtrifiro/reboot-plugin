---
id: theater-chain-09
project: theater-chain
source: "theater-chain/reboot-findings.md §9"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - web-app/SKILL.md
  - deploy/SKILL.md
tags: [auth, index-gap]
cluster: "4.1"
duplicate_of: cineloop-30
still_applies: unknown
status: Resolved
resolved_by: "web-app/SKILL.md § Auth in Web Apps; build/SKILL.md § Step 4 — Authorizers"
---

# allowed_origins missing from the web-app skill

**What happened.** The backend logs on every boot: "`Application(oauth=...)` is running without `allowed_origins=[...]`. Under `rbt dev run` that works - `http://localhost(:*)?` is allowed automatically - but the same configuration will fail to deploy to production." The web-app skill's "Auth in Web Apps" section covers `oauth=`, providers, cookies, and `token_verifier=` in detail and never mentions `allowed_origins`, the parameter a standalone web app needs and a same-origin chat app does not (the SPA is served from `:5173` in dev and its own hostname in production). The runtime warning fires after the code is written.

**Expected.** Add it to `Application(...)` in the web-app skill's auth section, with the dev-versus-prod note.

**Repro.** Not recorded.

**Where in the skills.** `web-app/SKILL.md`, "Auth in Web Apps". Duplicates `reboot-air-141-12`.

**Checked at 1.6.0.** Partly addressed. `deploy/SKILL.md:20,92,110` now covers `allowed_origins`, but `web-app/SKILL.md` still does not mention it (grep returned nothing).
