---
id: reboot-visualization-04
project: reboot-visualization
source: "v 1.4.1 Reboot/reboot-visualization/docs/reboot-learnings 03.md §4"
reboot_version: 1.4.0
severity: unrated
target: plugin
names:
  - python/references/servicer-transaction.md
  - python/references/scheduling-basic.md
tags: [cost, error-text, testing, negative-space]
cluster: ""
duplicate_of: theater-network-13
still_applies: no
status: Resolved
resolved_by: "python/references/scheduling-basic.md § Scales as; python/references/servicer-transaction.md § Errors you will see"
---

# Reading an actor early in a Transaction that schedules on it at commit is an upgrade deadlock under concurrency

**What happened.** `hold_seats` began with `Showing.get` (validate room ready / seat bounds) and ended by scheduling `note_seat` on the same Showing. Fine serially; under the lab's storms (16-20 concurrent holds) every transaction held a shared lock on the Showing from the read and then waited to upgrade to exclusive at commit for the schedule. Symptom: `HoldSeats` 503s after exactly 30s (`Timed out waiting … to upgrade to exclusive lock`) plus fast 503s from retries. A pre-scan `Seat.get` before `Seat.hold` has the same shape per seat. Fix: a transaction should only READ actors it will not lock for writing, and should not read what it can validate purely or learn from the write's own abort; validation became a pure label parse, `StateNotConstructed` from `Seat.hold` maps to `NoSuchSeat`, and a taken seat's abort carries the holder's name. After: 16/16 simultaneous holds on different seats land in parallel; 20-on-1 yields one winner and 19 typed rejections. Platform recommendations: detect upgrade deadlocks locally and abort a victim in milliseconds (wound-wait/wait-die) instead of both sides burning 30s; name the contended actor (and peer) in the timeout instead of advising 'retry the transaction', which re-deadlocks; a dev-mode check or lint for a Transaction that reads an actor it later locks exclusively (write or cross-actor `schedule()`), which covers items 3 and 4; document that a read pins a shared lock for the transaction's lifetime and that `schedule()` on a foreign actor makes it an exclusive-lock participant at commit. Why nothing else caught it: every other exercise was serial (unit suite, manual walkthrough), each half is individually idiomatic, six green tests and a flawless demo coexisted with the bug; dev-mode effect validation re-runs methods serially so the class is invisible to it, and the original theater app avoided the pattern only through a code comment.

**Expected.** Source asks for the lock facts above to be documented where Transactions are taught, plus the runtime changes listed.

**Repro.** 16-20 concurrent `hold_seats` transactions that each read the Showing then schedule `note_seat` on it.

**Where in the skills.** `servicer-transaction.md`, `scheduling-basic.md`. Same root as theater-network-13 (read then schedule upgrades the shared lock).

**Checked at 1.6.0.** `scheduling-basic.md` § Scales as says a transaction that read the actor then schedules on it upgrades its shared lock to exclusive; `servicer-transaction.md` § Errors you will see maps `Cannot upgrade shared lock to exclusive` to 'don't read before scheduling'. At 1.6.0 transactions declare `Shared()`/`Exclusive()` mode. The 1.4.0 timeout wording (`Timed out waiting … to upgrade to exclusive lock`), the serial-testing blind spot and the lint request are not recorded.
