---
id: cineloop-01
project: cineloop
source: "cineloop/reboot-findings.md §1 (Part 1)"
reboot_version: 1.4.1
severity: unrated
target: positive
names:
  - python/references/state-collections.md
  - python/references/state-actor-decomposition.md
tags: [pattern]
cluster: "E"
still_applies: unknown
status: Resolved
resolved_by: "python/references/patterns-cross-actor-reads.md § Do this; python/references/state-collections.md § Do this"
---

# The actor boundary is the concurrency design (seats inline on one Showing)

**What happened.** All ~200 seats of a showing were put on ONE `Showing` actor as inline `list[Seat]` sub-records rather than one actor per seat. Because Reboot serializes writers per actor this gave: atomic multi-seat holds (one writer body, no 2PC, no compensation); a cart cap (8 seats) that cannot drift because it is checked in the same writer that grants the hold; no double-booking (two patrons racing for F-12 are ordered, the loser gets a typed `SeatUnavailableError`). Making `Seat` its own `Type` (which the 'decompose aggressively' guidance superficially points at) would have made each of these a distributed transaction over up to 8 actors. The state-collections test ('does the item have identity, lifecycle, or methods of its own?') is right and a seat fails all three. Lesson: group into one actor the things that must change together; split into separate actors the things that must scale independently.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Positive pattern; kept as a candidate for a `patterns-*` reference (proposal task E). The plugin gap this implies is item 14 (cohesion counter-test). Compare theater-network-01, which reached the opposite design (per-seat actors) and had to rework it.
