---
id: findings-board-01
project: findings-board
source: "findings-board/FINDINGS.md § reboot.bdd, item 1"
reboot_version: 1.6.0
severity: yellow
target: bdd
names: []
tags: [testing, error-text]
cluster: ""
still_applies: unknown
status: Resolved
resolved_by: "python/references/testing-features.md § Errors you will see"
---
# A backtick inside a quoted step value breaks the step

**What happened.** ``... has `cards[0].title="`rbt generate` dies"` `` fails "Step definition is not found": the clause parser splits on the inner backticks, with no hint that the value is the cause. Titles in this domain are full of code spans. Workaround: assert with `containing` on a backtick-free substring.

**Expected.** Backticks inside a quoted value are kept, or the error names the value.

**Repro.** Assert a field whose quoted value contains a backtick code span.

**Where in the skills.** None.

**Resolution (2026-10-10).** Rows in `testing-features.md` § Errors you will see: a backtick inside a quoted value; `with` clauses after the actor; a recall inside a JSON5 literal.
