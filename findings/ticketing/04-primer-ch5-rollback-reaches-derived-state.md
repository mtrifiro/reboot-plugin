---
id: ticketing-04
project: ticketing
source: "Punch List - Ticketing App Build Findings.md §4"
reboot_version: 1.4.1
severity: unrated
target: primer
names: []
tags: [pattern, testing]
cluster: "8.4"
still_applies: unknown
status: Open
resolved_by: ""
---

# Chapter 5: rollback reaches derived state too

**What happened.** When a multi-seat purchase fails on the last seat, the rollback covers the seats already bought, the order, and the event's denormalized map. The app's test suite asserts this.

**Expected.** One sentence in the chapter claiming it.

**Repro.** Not recorded.

**Where in the skills.** Primer Chapter 5 - Races and Deadlocks.
