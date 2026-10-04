---
id: theater-network-25
project: theater-network
source: "theater-network/docs/reboot-findings.md §25"
reboot_version: 1.4.0
severity: unrated
target: plugin
names:
  - python/references/scheduling-basic.md
tags: [pattern, negative-space]
cluster: "E"
still_applies: yes
status: Open
resolved_by: ""
---

# Async note channels reorder: fence them with the actor's own generation

**What happened.** Any materialized map fed by scheduled notes (`Showing.seat_map`, `Service`'s order board) has NO delivery-order guarantee between tasks. Two notes about the same seat can land in either order, and a writer that mutates seats without noting (`force_reset` in the reset workflow) leaves a window where a pre-reset HELD note lands after the map clear and becomes a permanent phantom, while the audit recomputes from seats and stays green. Pattern that closes it: (1) pick a per-entity monotonic value the authoritative actor already maintains (the seat's `hold_generation`, bumped on every transition); (2) stamp every note with it; (3) keep a per-entity high-water mark next to the materialized map and drop notes below it; (4) any workflow that mutates entities WITHOUT noting must write a fence (record the post-mutation generation, evict stale map entries) after each wave; (5) never clear the mark map. Corollary: batch the notes, one `note_seats` task per transaction, not one per seat. Implemented 2026-08-16; a test delivers the race's losing message by hand.

**Expected.** Not recorded.

**Repro.** Two scheduled notes for one seat delivered out of order; reset workflow mutating without noting.

**Where in the skills.** `scheduling-basic.md` (no delivery-order guarantee); candidate for `patterns-cross-actor-reads.md` (proposal task E).

**Checked at 1.6.0.** No statement about scheduled-task ordering or the generation-fence pattern found in `python/references/scheduling-basic.md` or elsewhere.
