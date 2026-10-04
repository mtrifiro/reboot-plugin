---
id: theater-network-13
project: theater-network
source: "theater-network/docs/reboot-findings.md §13"
reboot_version: 1.4.0
severity: unrated
target: plugin
names:
  - python/references/scheduling-basic.md
  - python/references/servicer-transaction.md
tags: [cost, negative-space, error-text]
cluster: "D"
still_applies: yes
status: Resolved
resolved_by: "python/references/patterns-load-and-benchmarking.md § Scales as; python/references/scheduling-basic.md § Scales as"
---

# schedule() is a write; dev-mode write throughput is global

**What happened.** Measured on 1.3.0. Scheduling on an actor writes that actor's task queue. A transaction that has already read the actor (any `self.state` access) and then schedules on it must upgrade its shared lock to exclusive, so concurrent chains on one actor collide even if they never touch a state field (`Cannot upgrade shared lock to exclusive`). Parallel chains therefore need their own actors: the `RoomBuilder` never reads showing state (inputs ride in on `build`), self-schedules its continuation and enqueues the showing's progress note as a plain brief acquisition. Per-write cost in `rbt dev` is flat and global (about 150-200ms): sequential awaits, `asyncio.gather` inside the transaction, batching more per task and 3 concurrent transactions all land within about 20% of the same total (about 5.5-6.5 constructor-writes/second). The dev runtime's durable-write path is the bottleneck, not request latency, so parallelism buys interleaving but not proportional wall-clock.

**Expected.** Not recorded. Source advice: plan UX around it by making partial state usable (built rows holdable immediately) rather than chasing total-completion time.

**Repro.** Not recorded beyond the measurements.

**Where in the skills.** `scheduling-basic.md`, `servicer-transaction.md` (Scales as).

**Checked at 1.6.0.** No mention of the shared-to-exclusive upgrade on schedule or the dev write throughput in `python/references/scheduling-basic.md` or `servicer-transaction.md`.
