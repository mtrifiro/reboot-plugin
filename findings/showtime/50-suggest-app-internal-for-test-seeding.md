---
id: showtime-50
project: showtime
source: "2026.08.18 reboot-findings.md Suggested skill improvements, bullet 7"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/testing-harness.md
tags: [seeding, testing]
cluster: "C"
duplicate_of: showtime-30
still_applies: yes
status: Resolved
resolved_by: "python/references/testing-harness.md § Do this"
---

# Testing references should show app_internal=True for seeding fixtures

**What happened.** The testing references never show `app_internal=True` used for seeding test fixtures that production seeds via `initialize`.

**Expected.** One line in `testing-harness.md` would make the PermissionDenied-on-seed failure self-explanatory.

**Repro.** Not recorded.

**Where in the skills.** `testing-harness.md`.

**Checked at 1.6.0.** Same as showtime-30: no `app_internal` in python/references/testing-*.md.
