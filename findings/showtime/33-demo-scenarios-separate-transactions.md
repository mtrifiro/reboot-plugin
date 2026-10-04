---
id: showtime-33
project: showtime
source: "2026.08.18 reboot-findings.md #33"
reboot_version: 1.4.1
severity: unrated
target: positive
names: []
tags: [pattern]
cluster: "E"
still_applies: unknown
status: Open
resolved_by: ""
---

# Multi-step demo scenarios must be separate transactions for spectators to see them

**What happened.** A transaction commits atomically, so subscribers never see intermediate state. 'Watch the seats flicker' requires the client to pace discrete commits (hold, pause, restore), not one server-side scenario transaction.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded (a thing that worked; keep it documented).
