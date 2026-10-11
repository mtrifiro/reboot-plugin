---
id: restaurant-app-3-08
project: restaurant-app-3
source: "restaurant-app-3/FINDINGS.md § Plugin skills, item 5"
reboot_version: 1.6.0
severity: green
target: plugin
names:
  - python/references/lifecycle-application-entry.md
  - python/references/stdlib-ordered-map.md
  - python/references/state-collections.md
tags: [contradiction]
cluster: ""
still_applies: yes
status: Resolved
resolved_by: "python/references/lifecycle-application-entry.md § Do this; python/references/stdlib-ordered-map.md § Do this"
---
# Three references disagree on registering `OrderedMap`

**What happened.** `lifecycle-application-entry.md` (line ~59) says a stdlib type is wired "in **two** places", its `servicers()` list and its library, and its reading list (line ~82) says `ordered_map.servicers()` + `ordered_map_library()`. `stdlib-ordered-map.md` (line ~76) and `state-collections.md` (line ~127) register `ordered_map_library()` alone. `OrderedMapLibrary` has its own `servicers()`; with only the library, every reservation scenario (inserts and ranges) passed.

**Expected.** One answer, stated in all three.

**Repro.** Register only `ordered_map_library()`; run an insert and a range.

**Where in the skills.** `python/references/lifecycle-application-entry.md`; `python/references/stdlib-ordered-map.md`; `python/references/state-collections.md`.

**Resolution (2026-10-10).** `lifecycle-application-entry.md` now says a stdlib type with a `<name>_library()` is wired once, in `libraries=[...]`, which brings its servicers (verified 1.6.0), matching `stdlib-ordered-map.md` and `state-collections.md`; its Never and its per-type list say the same.
