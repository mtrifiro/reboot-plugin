---
id: marquee-control-08
project: marquee-control
source: "v 1.4.1 Reboot/Archive/marquee-control/docs/reboot-learnings.md §2026-08-17 build session, bullet 8"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/servicer-transaction.md
  - python/references/patterns-load-and-benchmarking.md
tags: [cost, pattern]
cluster: ""
duplicate_of: theater-chain-17
still_applies: no
status: Resolved
resolved_by: "python/references/servicer-transaction.md § Never"
---

# Keep reads of the hot actor out of contended transactions (20 holds: 59.3 s to 13.4 s)

**What happened.** `Cart.add_seat` did `showing.get()` (for entry metadata) inside the transaction that also calls `showing.hold`. Under the lab's 20-concurrent-hold burst every queued transaction serialized behind that read+write span on the one Showing: 59.3 s for 20 holds. Sourcing the metadata from the static `Chain` directory (uncontended read, seat write untouched) cut the same burst to 13.4 s, 4.4x. Rule: a transaction's span on a contended actor should be the minimal write; every removable read shortens the whole convoy. Dev-mode effect validation re-runs each transaction body, roughly doubling the span; production would be faster.

**Expected.** Not recorded.

**Repro.** 20 concurrent `Cart.add_seat` transactions that read then hold on one Showing.

**Where in the skills.** `servicer-transaction.md`, `patterns-load-and-benchmarking.md`. Same gap as theater-chain-17.

**Checked at 1.6.0.** `servicer-transaction.md` § Never: 'Read an actor then write it as two calls — one writer returning what the caller needs was about 10x faster under contention'; `patterns-load-and-benchmarking.md` § Scales as has the numbers.
