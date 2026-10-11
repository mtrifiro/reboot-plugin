---
id: restaurant-3-05
project: restaurant-3
source: "restaurant-3/FINDINGS.md § Things that worked, item 1"
reboot_version: 1.6.0
severity: green
target: positive
names:
  - python/references/patterns-error-handling.md
tags: [pattern]
cluster: ""
still_applies: unknown
status: Open
resolved_by: ""
---
# Declared errors propagate across actors unchanged

**What happened.** `Check.open` re-raises `Floor.occupy`'s `TableOccupiedError` as `Check.OpenAborted(aborted.error)` and the scenario's `the attempt aborts with `TableOccupiedError` with `table_id="d1"` and `check_id="check-1"`` saw the payload intact.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** `python/references/patterns-error-handling.md`, as described.
