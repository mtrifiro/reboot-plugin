---
id: showtime-16
project: showtime
source: "2026.08.18 reboot-findings.md #16"
reboot_version: 1.4.1
severity: unrated
target: positive
names: []
tags: [testing]
cluster: "8.4"
still_applies: unknown
status: Open
resolved_by: ""
---

# rbt.down() / rbt.up(revision=...) make restart tests short

**What happened.** 'Hold expiry survives a restart' became a 10-line test. Schedules persisted with the transaction fire after the process dies.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded (a thing that worked; keep it documented).
