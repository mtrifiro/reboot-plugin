---
id: new-theater-04
project: new-theater
source: "new-theater/FINDINGS.md § reboot.bdd, item 1"
reboot_version: 1.6.0
severity: yellow
target: bdd
names:
  - python/references/testing-features.md
tags: [testing, negative-space]
cluster: ""
still_applies: unknown
status: Resolved
resolved_by: "python/references/testing-features.md § Errors you will see"
---
# A saved value can't be recalled inside a JSON5 literal

**What happened.** `showtimes=[{movie_id: <movie id>, starts_at: <free slot>}]` fails "must be JSON"; only a whole value (`showtimes=<request>`) is recalled. `testing-features.md` says values are JSON5 and recalls are bare `<name>`, but not that the two don't combine. Workaround: a custom step that saves the whole list.

**Expected.** Recalls work inside a JSON5 value, or `testing-features.md` says they don't.

**Repro.** Save two values, then use both inside one JSON5 list literal in a step.

**Where in the skills.** `python/references/testing-features.md`.

**Resolution (2026-10-10).** Rows in `testing-features.md` § Errors you will see: a backtick inside a quoted value; `with` clauses after the actor; a recall inside a JSON5 literal.
