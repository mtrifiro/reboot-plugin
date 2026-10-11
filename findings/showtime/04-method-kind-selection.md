---
id: showtime-04
project: showtime
source: "2026.08.18 reboot-findings.md #4"
reboot_version: 1.4.1
severity: unrated
target: positive
names: []
tags: []
cluster: "8.4"
still_applies: unknown
status: Open
resolved_by: ""
---

# Writer mutates one actor; cross-actor needs Transaction; leaving the system needs Workflow

**What happened.** The checkout touches the User cart plus up to 8 Showings, so it is a Transaction. No external calls anywhere, so no Workflows were needed. (Design-phase finding.)

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded (a thing that worked; keep it documented).
