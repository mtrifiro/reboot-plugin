---
id: reboot-air-141-12
project: reboot-air-141
source: "reboot-air/REBOOT_FINDINGS.md §12"
reboot_version: 1.4.1
severity: yellow
target: plugin
names:
  - web-app/SKILL.md
  - deploy/SKILL.md
tags: [auth, index-gap]
cluster: "4.1"
duplicate_of: cineloop-30
still_applies: unknown
status: Open
resolved_by: ""
---

# allowed_origins required for production but not in web-app skill

**What happened.** The backend logs on every start: "`Application(oauth=...)` is running without `allowed_origins=[...]`. Under `rbt dev run` that works - `http://localhost(:*)?` is allowed automatically - but the same configuration will fail to deploy to production." `allowed_origins` appeared in no reference in the skill; the web-app "Auth in Web Apps" section covered `oauth=`, `OAuthProviderByEnvironment`, `Development()`, provider credentials, `claims=`, and `store_tokens=` but not the one parameter mandatory for a browser SPA to deploy. Cost in dev: zero, which is the concern; first sign of trouble is a failed production deploy.

**Expected.** Add `allowed_origins=[...]` to the "Auth in Web Apps" numbered sequence at step 2 beside "before `rbt serve` / Reboot Cloud, set `prod=...`": list the SPA's origin, or pass `[]` for same-origin-only. Better still, show it in the `Application(...)` example.

**Repro.** Not recorded.

**Where in the skills.** `web-app/SKILL.md`, "Auth in Web Apps".

**Checked at 1.6.0.** Partly addressed. `deploy/SKILL.md:20,92,110` now covers `allowed_origins` and `python/references/testing-web-app.md:108` uses it, but `web-app/SKILL.md` still never mentions it (grep returned nothing) in its auth section or `Application(...)` example.
