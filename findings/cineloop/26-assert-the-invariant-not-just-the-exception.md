---
id: cineloop-26
project: cineloop
source: "cineloop/reboot-findings.md §17 (Part 3)"
reboot_version: 1.4.1
severity: unrated
target: positive
names:
  - python/references/testing-harness.md
tags: [testing, pattern]
cluster: "E"
still_applies: unknown
status: Open
resolved_by: ""
---

# Assert the invariant, not just the exception

**What happened.** The race test (`test_two_patrons_race_for_the_last_seat`) checks that one of two simultaneous grabs raised AND that the showing ends with exactly one held seat. The first assertion alone would pass even if the winner had corrupted the seat. The harness reference makes this point and it earned its place.

**Expected.** Not recorded.

**Repro.** Two patrons race for the last seat.

**Where in the skills.** Positive: an existing reference point confirmed useful.
