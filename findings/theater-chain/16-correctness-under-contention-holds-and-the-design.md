---
id: theater-chain-16
project: theater-chain
source: "theater-chain/reboot-findings.md §15"
reboot_version: 1.4.1
severity: unrated
target: positive
names:
  - python/references/state-collections.md
tags: [pattern, testing]
cluster: "E"
still_applies: unknown
status: Resolved
resolved_by: "python/references/state-collections.md § Do this"
---

# Correctness under contention holds and the design is why

**What happened.** 40 patrons, 200 seats, four concurrent rounds; every invariant held on every run. Stampede: all 40 click seat F10 simultaneously, exactly 1 wins and 39 get `SeatUnavailableError(status="held")`. Block: 40 patrons grab random pairs from a 20-seat pool, 9 win, 31 refused, winners' seats disjoint. Spread: 40 patrons take distinct seats, all succeed. Checkout: every holder buys at once, 40 orders, 99 seats sold. Cross-check: every patron's cart matched the seat map 40/40, no seat granted twice, none lost, statuses summed to 200. None of it needed optimistic locking, version numbers, or application retries: seats live inline on `Showing` so a hold is a single-actor `Writer` the runtime serializes, and `hold_seats` validates the whole batch before mutating anything so a partial hold is impossible and a typed `<Method>Aborted` rolls back for free. The source suggests saying in `state-collections.md` that the actor you pick is the lock you get; had seats been 200 actors, contention would have needed a transaction over up to 8 of them.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** `python/references/state-collections.md` (suggested addition: "the actor you pick is the lock you get").

**Checked at 1.6.0.** Not checked; this item is a record of what worked (target positive).
