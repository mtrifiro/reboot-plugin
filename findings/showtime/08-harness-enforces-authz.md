---
id: showtime-08
project: showtime
source: "2026.08.18 reboot-findings.md #8"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - web-app/SKILL.md
  - python/references/servicer-authorizer.md
  - python/references/testing-harness.md
tags: [contradiction]
cluster: "4.1"
duplicate_of: theater-chain-04
still_applies: yes
status: Open
resolved_by: ""
---

# The test harness enforces production-mode authorization though rbt dev run only warns

**What happened.** With no `authorizer()`, the first test run failed with `PermissionDenied` on `Showing.create` from a user context. `rbt dev run` merely warns.

**Expected.** For `oauth=` apps, write real authorizers before the test step; 'defer authorizers in dev' only postpones the failure from dev-run to pytest. The source's suggested fix is one sentence in web-app step 12: the `Reboot()` harness runs production-mode authorization, so write authorizers before the test step.

**Repro.** Not recorded.

**Where in the skills.** web-app SKILL.md step 12 (build flow) and its auth section say to omit `authorizer()` in early development; `servicer-authorizer.md` implies the harness behaviour but the build flow never says it. See also suggested improvement 1.

**Checked at 1.6.0.** web-app/SKILL.md:108-111 and python/references/servicer-authorizer.md:64-66 still say to omit `authorizer()` early; python/references/testing-harness.md:124 now states the harness runs production-mode authorization, but the web-app build flow does not warn.
