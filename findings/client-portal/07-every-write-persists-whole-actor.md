---
id: client-portal-07
project: client-portal
source: "client-portal/reboot-findings.md §7"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/state-actor-decomposition.md
  - python/references/state-collections.md
tags: [cost, pattern, negative-space]
cluster: "D"
still_applies: yes
status: Open
resolved_by: ""
---

# Every write persists the whole actor

**What happened.** A `Portal` carries its manifest (8,878 `ManifestEntry` records at peak). Writing one integer of progress re-serialises all of it, so a per-note progress counter costs the most on exactly the vaults worth watching. Measured, the cost was not wall-clock: throughput was about 11-13 notes/minute with per-note writes and with batches of fifty; the Drive download dominates. The saving is load on the state store, not speed.

**Expected.** Keep large collections off actors that are written often, or write the frequently-changing part to a small actor of its own. Do not assume the write is the bottleneck; measure before optimising.

**Repro.** Not recorded beyond the measurement described.

**Where in the skills.** `python/references/state-actor-decomposition.md`, `python/references/state-collections.md`.

**Checked at 1.6.0.** `state-actor-decomposition.md` discusses writer serialization but no reference says that every write persists the whole actor state.
