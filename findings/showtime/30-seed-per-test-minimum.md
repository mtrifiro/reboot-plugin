---
id: showtime-30
project: showtime
source: "2026.08.18 reboot-findings.md #30"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/testing-harness.md
  - feature/SKILL.md
tags: [seeding, testing, pattern]
cluster: "C"
still_applies: yes
status: Open
resolved_by: ""
---

# Seed per-test minimum, not the production catalog

**What happened.** Running the real `initialize` (61 actors, 48x200-seat maps, doubled by effect validation) in every test would dominate the suite. Pattern that kept 12 tests at about 60s total: most tests create one Showing through an `app_internal=True` context; only stories about the catalog (dashboard, overview) pay for full `initialize`. The source adds that the testing references never show `app_internal=True` used for seeding (suggested improvement 7).

**Expected.** One line in `testing-harness.md` would make the PermissionDenied-on-seed failure self-explanatory.

**Repro.** Not recorded.

**Where in the skills.** `testing-harness.md`; `feature` skill test-setup guidance (proposal task C).

**Checked at 1.6.0.** grep `app_internal` in python/references/testing-*.md returns nothing; hits are only in web-app/SKILL.md:179 and python/references/auth-external-api-calls.md.
