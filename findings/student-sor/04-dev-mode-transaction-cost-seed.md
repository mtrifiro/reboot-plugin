---
id: student-sor-04
project: student-sor
source: "student-sor/reboot-findings.md §4"
reboot_version: 1.5.0
severity: unrated
target: plugin
names:
  - python/references/lifecycle-initialize-hook.md
  - python/references/stdlib-ordered-map.md
tags: [cost, seeding]
cluster: "D"
still_applies: yes
status: Resolved
resolved_by: "python/references/patterns-load-and-benchmarking.md § Do this; python/references/lifecycle-seeding.md § Scales as"
---

# Dev-mode transactions cost about 1.5 s each, so a realistic seed needs bulk methods

**What happened.** Measured: the first seeder issued one transaction per enrollment and per grade (roughly 3,600 calls). `Institution.admit_student`, a transaction with four hops (two reads, one create, one `OrderedMap` insert), took about 1.5 s wall time in `rbt dev run` with the effect-validation re-run included; 193 admits took nearly five minutes before any history was written. Test cases with about twenty-five mutations run 35 to 45 s each. The seed was redesigned around `Student.import_history` (one transaction per student creating every attempt, roster inserts batched per term with the bulk `entries=` form of `OrderedMap.insert`, index refreshed once), one student at a time. Details in the project's `DECISIONS.md` item 14.

**Expected.** Guidance on dev-mode transaction cost and on turning effect validation off for bulk loads; the seeder is a common first-launch need and the naive shape does not scale past a few dozen records.

**Repro.** Not recorded.

**Where in the skills.** `python/references/lifecycle-initialize-hook.md`; no seeding or cost reference exists.

**Checked at 1.6.0.** No reference under `python/references/` gives dev-mode transaction cost or advice on disabling effect validation for bulk loads (grep for `effect validation` finds only the determinism warnings in `servicer-writer.md`, `servicer-transaction.md`, `scheduling-recurring.md`).
