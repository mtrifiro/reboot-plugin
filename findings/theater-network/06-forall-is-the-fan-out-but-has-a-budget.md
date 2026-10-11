---
id: theater-network-06
project: theater-network
source: "theater-network/docs/reboot-findings.md §6"
reboot_version: 1.4.0
severity: unrated
target: plugin
names:
  - python/references/rpc-forall.md
tags: [cost, negative-space]
cluster: "D"
still_applies: yes
status: Resolved
resolved_by: "python/references/patterns-load-and-benchmarking.md § Limits"
---

# Service.forall(ids) is the fan-out; budget it

**What happened.** `Service.forall(ids).method(context)` is framework-native, batches internally and returns results in input order; a hand-rolled loop of awaits is slower and more code. But `forall` over a handful of actors (`showtimes`, `network`) is fine and over about 150 (a seat map) it times out (see item 8). The `audit` keeps the big fan-out deliberately as an on-demand recompute.

**Expected.** Not recorded.

**Repro.** `forall` over ~150 actors times out; over a handful works.

**Where in the skills.** `python/references/rpc-forall.md` (Limits / Scales as).

**Checked at 1.6.0.** `python/references/rpc-forall.md` recommends `forall` over hand-rolled gather but states no size or time budget.
