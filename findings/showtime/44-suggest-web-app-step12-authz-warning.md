---
id: showtime-44
project: showtime
source: "2026.08.18 reboot-findings.md Suggested skill improvements, bullet 1"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - web-app/SKILL.md
  - python/references/servicer-authorizer.md
tags: [contradiction]
cluster: "4.1"
still_applies: yes
status: Open
resolved_by: ""
---

# web-app SKILL.md step 12 should warn that the harness enforces authz

**What happened.** The auth section says 'omit `authorizer()` in early development; the dev-run warning is your TODO list', but the build flow's test step then fails with `PermissionDenied`.

**Expected.** One sentence: 'the `Reboot()` harness runs production-mode authorization, so write authorizers before the test step.' (`servicer-authorizer.md` implies it; the build flow never says it.)

**Repro.** Not recorded.

**Where in the skills.** web-app SKILL.md step 12; `servicer-authorizer.md`.

**Checked at 1.6.0.** web-app/SKILL.md:108-111 still says omit `authorizer()`; no step-12 warning. Same evidence as showtime-08.
