---
id: cineloop-12
project: cineloop
source: "cineloop/reboot-findings.md §12 (Part 1)"
reboot_version: 1.4.1
severity: unrated
target: positive
names:
  - python/references/stdlib-ordered-map.md
tags: [pattern]
cluster: "E"
still_applies: unknown
status: Open
resolved_by: ""
---

# Index keys are an API decision (zero-padded monotonic key in an OrderedMap)

**What happened.** The patron's order index is an `OrderedMap` (orders accumulate forever, so not a `list[str]`), keyed by `f"{sequence:012d}"` from a monotonic per-user counter. That is deterministic (retry-safe), sorts in purchase order, and makes 'newest first' a plain `reverse_range` with no secondary index. A timestamp key fails the first test; a UUID key fails the second and third.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Positive pattern; kept as a candidate for a `patterns-*` reference (proposal task E).
