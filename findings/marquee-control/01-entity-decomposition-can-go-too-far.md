---
id: marquee-control-01
project: marquee-control
source: "v 1.4.1 Reboot/Archive/marquee-control/docs/reboot-learnings.md §2026-08-17 build session, bullet 1"
reboot_version: 1.4.1
severity: unrated
target: positive
names:
  - python/references/state-collections.md
  - python/references/patterns-cross-actor-reads.md
tags: [pattern, cost]
cluster: ""
duplicate_of: cineloop-01
still_applies: no
status: Resolved
resolved_by: "python/references/state-collections.md § Do this; python/references/patterns-cross-actor-reads.md § Do this"
---

# Entity decomposition can go too far: seats inline on the Showing, the directory denormalized into Chain

**What happened.** Theater-network made every seat its own actor and paid for it (fan-out readers blow request budgets; 216-actor room builds take about 16 s in a Workflow, 54 s in a transaction). Here each Showing owns its 200 seats inline as `list[Seat]` sub-records: one actor per seat map means one reactive subscription per viewer and single-writer serialization per showing, exactly the contention domain of a real auditorium. Theaters have no behavior of their own, so the 12-theater directory is denormalized into a singleton `Chain` actor (one read for the whole dashboard rail instead of a 12+48 reader fan-out, which never gets a reactive first frame).

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** `state-collections.md`, `patterns-cross-actor-reads.md`. Same lesson as cineloop-01; the directory half is showtime-23.

**Checked at 1.6.0.** `state-collections.md` § Do this step 1 keeps all-or-none items inline 'because the actor is the lock' (seats inline held every invariant under 40 concurrent holds); `patterns-cross-actor-reads.md` § Do this step 1 names inline `list[Seat]`.
