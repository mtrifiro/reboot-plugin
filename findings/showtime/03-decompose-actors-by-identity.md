---
id: showtime-03
project: showtime
source: "2026.08.18 reboot-findings.md #3"
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

# Decompose into actors by identity, not by size

**What happened.** Anything with its own lifecycle/methods is its own state `Type`; parents store string IDs. Seats are the counter-example: they have no life apart from their Showing and the auditorium fixes their count (~200), so they live inline as `dict[str, Seat]`. (Design-phase finding.)

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded (a thing that worked; keep it documented).
