---
id: theater-network-08
project: theater-network
source: "theater-network/docs/reboot-findings.md §8"
reboot_version: 1.4.0
severity: unrated
target: plugin
names:
  - python/references/rpc-forall.md
  - python/references/servicer-reader.md
  - python/references/scheduling-basic.md
tags: [cost, pattern, negative-space]
cluster: "D"
still_applies: yes
status: Open
resolved_by: ""
---

# Fan-out readers have a hard request budget; materialize on write

**What happened.** A reader that reads about 150 other actors does not complete inside the request window, reactive or one-shot, chunked or not, and surfaces as `Unavailable: ping timeout` (503). `occupancy`-sized responses occasionally squeak through warm; a seat map never did. Architectural answer: materialize on write, not compute on read. Every seat mutation schedules an async `note_seat` to its Showing (from the Cart transaction, since only a `TransactionContext` may schedule on a foreign actor), the Showing keeps `seat_status`/`seat_holder` maps, and the seat-map reader becomes a state-only read costing milliseconds and safe to subscribe. The write is off the customer's critical path and commits with the transaction, so a rolled-back hold notes nothing. Keep one deliberately expensive recompute (the audit) as the check for paths that forget to note; run it on demand, never as a subscription.

**Expected.** Not recorded.

**Repro.** Seat-map reader over ~150 seat actors.

**Where in the skills.** Proposal task D (Scales as / load patterns) and E (patterns-cross-actor-reads).

**Checked at 1.6.0.** `python/references/servicer-reader.md` and `rpc-forall.md` give no request-budget number or the materialize-on-write pattern.
