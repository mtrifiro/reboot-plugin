---
id: new-theater-03
project: new-theater
source: "new-theater/FINDINGS.md § Framework, item 3"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - python/references/patterns-cross-actor-reads.md
tags: [cost, pattern]
cluster: ""
still_applies: unknown
status: Resolved
resolved_by: "python/references/patterns-cross-actor-reads.md § Scales as"
---
# An OrderedMap hop inside a fan-out multiplies its cost

**What happened.** A city listing fanning out to 11 `Screen` readers that each `range` an `OrderedMap` and read ~5 `Showtime` summaries took ~3 s under `rbt dev run` even with effect validation disabled (one such screen read: 0.5 s; eleven in parallel: 3.3 s). Moving each screen's live schedule inline and dropping per-showtime reads from the listing fixed it.

**Expected.** A line in `patterns-cross-actor-reads.md`: an `OrderedMap` hop inside a fan-out multiplies its cost.

**Repro.** A reader fanning out to ~11 actors, each of which ranges an `OrderedMap` and reads ~5 further actors.

**Where in the skills.** `python/references/patterns-cross-actor-reads.md`.

**Resolution (2026-10-10).** `patterns-cross-actor-reads.md` § Scales as: an `OrderedMap` hop inside a fan-out multiplies its cost; keep what a listing needs inline on the fanned-out actor.
