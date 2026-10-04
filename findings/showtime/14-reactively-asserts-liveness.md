---
id: showtime-14
project: showtime
source: "2026.08.18 reboot-findings.md #14"
reboot_version: 1.4.1
severity: unrated
target: positive
names: []
tags: [testing, pattern]
cluster: "E"
still_applies: unknown
status: Open
resolved_by: ""
---

# `reactively()` in tests is the honest way to assert liveness

**What happened.** It exercises the same push channel the React hooks use. Loop until the expected state; intermediate snapshots are normal.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded (a thing that worked; keep it documented).
