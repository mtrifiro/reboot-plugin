---
id: theater-network-01
project: theater-network
source: "theater-network/docs/reboot-findings.md §1"
reboot_version: 1.4.0
severity: unrated
target: positive
names:
  - python/references/state-actor-decomposition.md
  - python/references/rpc-forall.md
tags: [pattern]
cluster: "E"
still_applies: unknown
status: Resolved
resolved_by: "python/references/patterns-cross-actor-reads.md § Do this"
---

# Lock granularity is the design, not an optimization

**What happened.** First version kept occupancy counters and a taken-seats index on the `Showing`, updated by the same transaction that held the seats. Twenty concurrent customers produced `SystemAborted: 'Unavailable': Timed out waiting 30.0s to acquire exclusive lock; retry the transaction.` Every hold took an exclusive lock on the room, the burst serialized into a convoy and the tail died on the lock deadline. Per-seat actors buy nothing if every hold still writes one shared actor. Fix: a per-customer `Cart` owns the hold transaction (cart plus requested seats only); the `Showing` is read-mostly; occupancy is derived by readers via `Seat.forall(ids).get(context)`. After the rework the same 20-way race passes with exactly one winner and nineteen typed rejections.

**Expected.** Rule of thumb from the source: the write path must touch only actors whose contention is intrinsic to the domain (a seat two people want, a cart owned by one person); any other bookkeeping belongs in a reader.

**Repro.** Twenty concurrent customers holding seats on one showing (first design). Exact test not recorded beyond that.

**Where in the skills.** Positive pattern; no skill states it. Related to cineloop-01 (the opposite boundary choice, inline seats on one actor).
