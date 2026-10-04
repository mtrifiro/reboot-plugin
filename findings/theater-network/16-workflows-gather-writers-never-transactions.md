---
id: theater-network-16
project: theater-network
source: "theater-network/docs/reboot-findings.md §16"
reboot_version: 1.4.0
severity: unrated
target: plugin
names:
  - python/references/servicer-workflow.md
tags: [negative-space, cost]
cluster: "4.1"
still_applies: yes
status: Resolved
resolved_by: "python/references/servicer-workflow-calls.md § Never"
---

# Workflows: gather writers, never gather transactions

**What happened.** Inside one workflow iteration `asyncio.gather` over WRITER calls is fine (room build does about 20 concurrently). The same gather over TRANSACTION calls (eight `Cart.hold_seats` at once) deadlocked: sibling transactions contend through their shared workflow root and every one dies at the 30s seat-lock deadline. Issue transactions from a workflow sequentially; the concurrency win over the old tick-transaction design (which nested them at 2PC cost) is still about 10-20x. Related traps: (a) the crowd engine is now a `context.loop` workflow, not a self-scheduling tick transaction, because the tick serialized every operation in one transaction and capped the crowd at about 1 op/s; (b) synchronized hold expirations (fixed 45s) storm the carts the loop is confirming against, so jitter the windows and check the live map before acting on a hold that may have lapsed; (c) `seat_map.rows_built` does not exist: scoped workflow calls type as Any, so mypy cannot catch a wrong field on their results.

**Expected.** Not recorded.

**Repro.** Eight concurrent `Cart.hold_seats` transaction calls gathered in one workflow iteration.

**Where in the skills.** `servicer-workflow.md` (Never).

**Checked at 1.6.0.** `python/references/servicer-workflow.md` does not mention gathering transactions or the deadlock (grep for gather found nothing there; `rpc-forall.md` discusses gather for plain calls).
