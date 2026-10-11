---
id: mattprd-06
project: mattprd
source: "2026.08.22 REBOOT_FINDINGS.md §6"
reboot_version: 1.4.1
severity: green
target: framework
names:
  - python/references/stdlib-ordered-map.md
tags: [negative-space]
cluster: "8.4"
still_applies: unknown
status: Resolved
resolved_by: "python/references/stdlib-ordered-map.md § Limits"
---

# OrderedMap.range/reverse_range have no exclusive-start

**What happened.** `start_key` is inclusive and the stdlib reference advises 'add a one-byte suffix or remember to skip the duplicate first row'. Every paginated reader (three in this app) ends up with the same skip-the-cursor-row loop and a `limit + 1` fetch.

**Expected.** An `after_key=` (exclusive) parameter or an `exclusive_start: bool` flag on `range`/`reverse_range`.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.
