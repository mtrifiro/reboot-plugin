---
id: restaurant-app-3-16
project: restaurant-app-3
source: "restaurant-app-3/FINDINGS.md § Things that worked, item 4"
reboot_version: 1.6.0
severity: green
target: positive
names:
  - python/references/state-actor-decomposition.md
  - python/references/patterns-common-gotchas.md
tags: [pattern]
cluster: ""
still_applies: unknown
status: Open
resolved_by: ""
---
# One-way call guidance shaped the design up front; no deadlocks

**What happened.** The writer-cycle warning fixed the call graph before any code: the floor writes checks, checks write the kitchen, nothing writes back. There were no deadlocks.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** `python/references/state-actor-decomposition.md`; `python/references/patterns-common-gotchas.md`.
