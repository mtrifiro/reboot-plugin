---
id: showtime-10
project: showtime
source: "2026.08.18 reboot-findings.md #10"
reboot_version: 1.4.1
severity: unrated
target: positive
names: []
tags: [auth]
cluster: "E"
still_applies: unknown
status: Open
resolved_by: ""
---

# Servicer-to-servicer calls count as app-internal

**What happened.** Even when the original caller is an external user, `User.add_seat` (called by a patron) can invoke internal-only `Showing.hold_seat`, and the scheduled `expire_hold` passes the same gate. Confirmed by the passing suite.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded (a thing that worked; keep it documented).
