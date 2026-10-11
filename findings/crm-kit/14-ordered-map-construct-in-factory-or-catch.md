---
id: crm-kit-14
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §2"
reboot_version: 1.6.0
severity: unrated
target: framework
names:
  - python/references/stdlib-ordered-map.md
tags: [negative-space, error-text]
cluster: "4.1"
duplicate_of: reboot-crm-71
still_applies: no
status: Resolved
resolved_by: "python/references/stdlib-ordered-map.md § Limits"
---

# An OrderedMap exists only after construction or its first insert, and has no exists

**What happened.** A read of an `OrderedMap` before its construction or first insert raises; there is no `exists`. Rule: construct each `OrderedMap` in its owner's factory, or catch `OrderedMap.SearchAborted` as "empty".

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `python/references/stdlib-ordered-map.md` § Limits (line ~146) says catch `SearchAborted`/`RangeAborted` as empty or construct up front; `errors.md` indexes `OrderedMap.SearchAborted: aborted with 'StateNotConstructed'`.
