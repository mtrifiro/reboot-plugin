---
id: cineloop-10
project: cineloop
source: "cineloop/reboot-findings.md §10 (Part 1)"
reboot_version: 1.4.1
severity: unrated
target: positive
names:
  - python/references/servicer-reader.md
tags: [pattern, cost]
cluster: "E"
still_applies: unknown
status: Resolved
resolved_by: "python/references/patterns-cross-actor-reads.md § Do this"
---

# Give the lobby its own cheap summary reader

**What happened.** `seat_map` ships 200 seat views; the lobby shows 48 showings. Calling `seat_map` 48 times would be about 9,600 seat views per frame, re-pushed on every hold anywhere in the chain. `summary` returns the same actor's state as counts (available/held/sold plus how many are mine): same actor, same reactivity, about 2% of the payload. 'One actor can and should expose several readers at different granularities. Reader shape is a performance API.'

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Positive pattern; kept as a candidate for a `patterns-*` reference (proposal task E). The plugin gap is item 20.
