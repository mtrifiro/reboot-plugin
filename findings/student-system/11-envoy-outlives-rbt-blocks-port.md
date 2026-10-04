---
id: student-system-11
project: student-system
source: "student-system/reboot-findings.md §11"
reboot_version: 1.5.0
severity: unrated
target: plugin
names:
  - run/SKILL.md
  - dashboard/SKILL.md
tags: [operations, negative-space, error-text]
cluster: "F"
still_applies: yes
status: Open
resolved_by: ""
---

# Envoy outlives both rbt dev run and rbt dashboard, then blocks the port

**What happened.** Killing the backend left an `envoy` listening on 9992; killing the dashboard left one on 9871. The next start fails with "cannot bind ... Address already in use" and a message asking to report a Reboot bug. `lsof -t -iTCP:<port> -sTCP:LISTEN | xargs kill` became part of the app's restart routine. Repeat of Reboot Air 8 (reboot-air-08).

**Expected.** Envoy should die with its parent, and the `run` skill should say how to stop an app.

**Repro.** Not recorded.

**Where in the skills.** `run/SKILL.md` (no stop/restart section).

**Checked at 1.6.0.** `run/SKILL.md` has no stop, kill or restart guidance (grep for stop/kill/expunge found only unrelated lines).
