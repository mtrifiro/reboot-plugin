---
id: showtime-02
project: showtime
source: "2026.08.18 reboot-findings.md #2"
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

# Zero-value defaults are mandatory on every Field(tag=N)

**What happened.** Non-zero defaults are rejected at import. Domain defaults belong in the constructor method gated on `context.constructor`. (Design-phase finding.)

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded (a thing that worked; keep it documented).
