---
id: showtime-39
project: showtime
source: "2026.08.18 reboot-findings.md #39"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/servicer-transaction.md
tags: [negative-space, cost]
cluster: "4.1"
still_applies: yes
status: Resolved
resolved_by: "python/references/servicer-transaction.md § Never"
---

# Keep one global actor-touch order across every cross-actor transaction

**What happened.** Showtime's cleanup paths all go Showing->User (`expire_hold`, `_wipe_seat`); a chain-wide refund written as a `User` transaction would go User->Showing, an inversion that, with the ambient crowd firing `expire_hold` constantly, risks two transactions each holding what the other needs. Moving the refund onto the `Lab` actor (read tickets via a reader, then Showing->User writers) restores a single order.

**Expected.** Treat consistent ordering as the builder's responsibility; the references never discuss lock ordering between transactions.

**Repro.** Not recorded.

**Where in the skills.** Not recorded; `servicer-transaction.md` is the natural home.

**Checked at 1.6.0.** python/references/servicer-transaction.md and upgrade/migrations/1.6.0/transaction-mode.md discuss lock mode (exclusive/shared) and upgrade deadlocks, but nothing on touch ordering across transactions.
