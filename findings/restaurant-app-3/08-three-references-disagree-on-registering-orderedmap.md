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
status: Open
resolved_by: ""
---
# Three references disagree on registering `OrderedMap`

**What happened.** `lifecycle-application-entry.md` (line ~59) says a stdlib type is wired "in **two** places", its `servicers()` list and its library, and its reading list (line ~82) says `ordered_map.servicers()` + `ordered_map_library()`. `stdlib-ordered-map.md` (line ~76) and `state-collections.md` (line ~127) register `ordered_map_library()` alone. `OrderedMapLibrary` has its own `servicers()`; with only the library, every reservation scenario (inserts and ranges) passed.

**Expected.** One answer, stated in all three.

**Repro.** Register only `ordered_map_library()`; run an insert and a range.

**Where in the skills.** `python/references/lifecycle-application-entry.md`; `python/references/stdlib-ordered-map.md`; `python/references/state-collections.md`.
