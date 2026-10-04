---
id: theater-chain-18
project: theater-chain
source: "theater-chain/reboot-findings.md §17b"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/servicer-transaction.md
tags: [cost, testing]
cluster: "D"
still_applies: yes
status: Open
resolved_by: ""
---

# Transaction cost scales with participants not calls

**What happened.** Checkout batching was measured twice with opposite conclusions because the first workload was wrong. Round C (2 seats per patron) collapses about 2.5 calls into 1; A/B twice against a control round showed no measurable effect and the author was ready to revert. Round E (full 8-seat basket, 8 distinct hold ids, 200 confirm calls collapsing to 25), same code and design: old-1 C 15.4s / E2 30.7s; new-1 C 15.6s / E2 25.7s; old-2 C 15.1s / E2 30.2s; new-2 C 15.9s / E2 25.7s: about 16%, replicated to within 15 ms. The author's general lesson (not Reboot-specific): a load test that under-exercises the path will report "no effect" with total confidence. Also: 8x fewer calls bought 16%, not 8x. Each checkout is a Transaction touching a `Showing`, an `Order`, an `OrderedMap` and its `Node`s; cutting calls to one participant does not cut the participant count.

**Expected.** If per-participant transaction coordination is the dominant cost at this scale, say so in `servicer-transaction.md`: it changes how you optimize (fewer participants, not fewer calls).

**Repro.** Not recorded.

**Where in the skills.** `python/references/servicer-transaction.md`.

**Checked at 1.6.0.** Still absent. `python/references/servicer-transaction.md` has no participant-cost guidance (grep for participants / cost found nothing relevant).
