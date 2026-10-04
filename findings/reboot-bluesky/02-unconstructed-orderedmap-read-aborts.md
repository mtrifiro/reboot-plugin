---
id: reboot-bluesky-02
project: reboot-bluesky
source: "REBOOT_FINDINGS.md §2"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/stdlib-ordered-map.md
  - python/references/rpc-refs.md
tags: [negative-space, contradiction]
cluster: "4.1"
duplicate_of: student-system-02
still_applies: no
status: Obsolete
resolved_by: ""
---

# Reading an unconstructed OrderedMap aborts instead of reading empty

**What happened.** `search`/`range` on a never-inserted map raise `OrderedMap.SearchAborted: StateNotConstructed`. This breaks the otherwise-consistent zero-value story ('a reader call on a non-existent actor returns the zero-valued state') and forces every app to eagerly construct maps (extra transaction participants on hot paths) or guard every read behind a denormalized count.

**Expected.** Reads on an unconstructed map behave as reads of an empty map, or the asymmetry is documented prominently in `stdlib-ordered-map.md`.

**Repro.** Not recorded.

**Where in the skills.** `stdlib-ordered-map.md`; `rpc-refs.md` (zero-value claim).

**Checked at 1.6.0.** python/references/stdlib-ordered-map.md:16-17 and :105-110 now state that reading an unconstructed map aborts with `StateNotConstructed`. (python/references/rpc-refs.md:105 still states the general zero-value rule without the exception.)
