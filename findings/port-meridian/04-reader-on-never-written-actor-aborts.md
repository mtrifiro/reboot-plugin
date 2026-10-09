---
id: port-meridian-04
project: port-meridian
source: "v 1.4.1 Reboot/port-meridian/docs/reboot-learnings 04.md §3"
reboot_version: 1.4.0
severity: unrated
target: plugin
names:
  - python/references/rpc-refs.md
tags: [negative-space, error-text]
cluster: "4.1"
duplicate_of: cineloop-33
still_applies: no
status: Open
resolved_by: ""
---

# A reader on a never-written actor aborts StateNotConstructed, even with no factory

**What happened.** A `Reader` on a never-written actor with no factory aborts with `StateNotConstructed` rather than returning zero-valued state, so singleton actors a UI subscribes to on page load need an explicit no-op `ensure` writer called from `initialize`.

**Expected.** Not recorded.

**Repro.** Subscribe to a reader on a singleton actor that nothing has written yet.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `python/references/rpc-refs.md` § Do this ("Does this actor exist?") now says a reader on a never-constructed actor aborts `StateNotConstructed` for every type, with or without a `factory=True` constructor, matching this observation (cineloop-33 had assumed only factory types abort); § Never warns against assuming zero-valued state. The `ensure`-from-`initialize` remedy for singletons is not described there.
