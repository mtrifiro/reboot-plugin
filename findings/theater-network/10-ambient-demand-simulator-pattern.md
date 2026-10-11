---
id: theater-network-10
project: theater-network
source: "theater-network/docs/reboot-findings.md §10"
reboot_version: 1.4.0
severity: unrated
target: positive
names:
  - python/references/scheduling-recurring.md
tags: [pattern]
cluster: "E"
still_applies: unknown
status: Open
resolved_by: ""
---

# The ambient-demand simulator pattern

**What happened.** A `Simulation` singleton with a self-rescheduling `tick` transaction (the documented cron shape) drives synthetic customers through real `Cart` transactions. Randomness is a deterministic LCG whose seed lives in state (writer bodies may re-execute so `random()` is forbidden, but advancing a seed is just state mutation). Durable by construction: killing the server leaves the pending tick to fire on restart. First confirmation on 1.3.0 that a Transaction may call another Transaction (`tick` -> `Cart.hold_seats`). Partially superseded: the tick-transaction shape capped the crowd at about 1 op/s and was replaced by a `context.loop` workflow (see item 16); the determinism rules (LCG seed in state, no `random()`) carried over.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Candidate for `patterns-time-and-randomness.md` (proposal task E). Note `scheduling-recurring.md` line ~45 uses `random.randint` in a writer.
