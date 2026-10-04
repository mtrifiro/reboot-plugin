---
id: showtime-05
project: showtime
source: "2026.08.18 reboot-findings.md #5"
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

# Typed errors are Models in errors=[...] and raising one rolls back the method

**What happened.** Raised as `<Type>.<Method>Aborted(ErrorModel(...))`; raising one rolls back the method's mutations automatically. Suited to 'seat already held'. (Design-phase finding.)

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded (a thing that worked; keep it documented).
