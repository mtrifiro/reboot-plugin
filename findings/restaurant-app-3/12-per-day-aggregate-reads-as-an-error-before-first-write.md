---
id: restaurant-app-3-12
project: restaurant-app-3
source: "restaurant-app-3/FINDINGS.md § Plugin skills, item 9"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - python/references/rpc-refs.md
  - python/references/patterns-cross-actor-reads.md
tags: [pattern, negative-space]
cluster: ""
still_applies: yes
status: Resolved
resolved_by: "python/references/patterns-cross-actor-reads.md § Do this"
---
# A per-day aggregate reads as an error before its first write

**What happened.** The natural design for "today's sales" is an actor keyed by date, built on its first settled check. Before that, the manager's sales page gets `StateNotConstructed` rather than zeros. `rpc-refs.md` (line ~65) documents the abort (the cineloop-33 family), but the design guidance never mentions it for period-keyed aggregates. restaurant-app-2 avoided it with a single ledger holding an `OrderedMap` of closed checks and a per-day totals map, so an empty day reads as zero.

**Expected.** A short pattern note: for date- or period-keyed aggregates, prefer a long-lived owner that answers for any date, or a reader that maps `StateNotConstructed` to the zero value; show the ledger shape.

**Repro.** A `DaySales` actor keyed by date; read it before any check settles that day.

**Where in the skills.** `python/references/rpc-refs.md`; `python/references/patterns-cross-actor-reads.md`.

**Resolution (2026-10-10).** `patterns-cross-actor-reads.md` § Do this, shape 7: a period-keyed aggregate gets a long-lived owner that answers for any period, or its reader catches the abort and returns the zero value.
