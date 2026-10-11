---
id: restaurant-app-3-18
project: restaurant-app-3
source: "restaurant-app-3/FINDINGS.md § Things that worked, item 6"
reboot_version: 1.6.0
severity: green
target: positive
names:
  - python/references/patterns-time-and-randomness.md
  - python/references/patterns-common-gotchas.md
tags: [pattern]
cluster: ""
still_applies: unknown
status: Open
resolved_by: ""
---
# Effect-validation notes removed a class of second-guessing

**What happened.** Knowing that bodies run twice and that `uuid4()` in a constructor is safe meant no time spent wondering whether a writer was safe to retry.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** `python/references/patterns-time-and-randomness.md`; `python/references/patterns-common-gotchas.md`.
