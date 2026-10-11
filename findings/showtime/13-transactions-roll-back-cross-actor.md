---
id: showtime-13
project: showtime
source: "2026.08.18 reboot-findings.md #13"
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

# Transactions roll back cross-actor

**What happened.** In the all-or-nothing checkout test, seat H2's successful `confirm_seat` was undone when the transaction later aborted on H1. No compensating writes needed.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded (a thing that worked; keep it documented).
