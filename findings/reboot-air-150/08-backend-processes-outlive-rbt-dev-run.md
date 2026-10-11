---
id: reboot-air-150-08
project: reboot-air-150
source: "reboot-air/reboot-findings.md §8"
reboot_version: 1.5.0
severity: unrated
target: plugin
names:
  - run/SKILL.md
tags: [operations, negative-space]
cluster: "F"
duplicate_of: reboot-crm-15
still_applies: yes
status: Resolved
resolved_by: "run/references/stop-restart-reset.md § Do this"
---

# Backend processes outlive rbt dev run

**What happened.** Killing the `rbt dev run` process (`pkill -f "rbt dev run"`) left two `python backend/src/main.py` children running and holding state. `rbt dev expunge` then succeeded while they were still up. Stopping cleanly needs `pkill -f backend/src/main.py` as well.

**Expected.** The `run` skill could mention how to stop the app, not only how to start it.

**Repro.** Not recorded.

**Where in the skills.** `run/SKILL.md`.

**Checked at 1.6.0.** `run/SKILL.md` has no stop/restart section.
