---
id: showtime-15
project: showtime
source: "2026.08.18 reboot-findings.md #15"
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

# mock.patch.object on a module global shortens durable timers in tests

**What happened.** `mock.patch.object(module, "HOLD_SECONDS", 1)` works because the servicer reads the module global at call time.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded (a thing that worked; keep it documented).
