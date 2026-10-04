---
id: student-system-08
project: student-system
source: "student-system/reboot-findings.md §8"
reboot_version: 1.5.0
severity: unrated
target: plugin
names:
  - python/references/servicer-writer.md
  - python/references/servicer-transaction.md
  - python/references/state-collections.md
tags: [negative-space, pattern, contradiction]
cluster: "4.1"
still_applies: unknown
status: Open
resolved_by: ""
---

# Child-actor ids come from uuid4() inside transactions; effect validation never objected

**What happened.** `Student.enroll`, `file_petition` and `apply_for_graduation` are transactions that mint `str(uuid4())`, construct a child actor with it and append the id to the student's state; `place_hold` (a writer) does the same. `servicer-writer.md` warns against persisting non-deterministic values from writers because bodies "re-execute under transient retries and dev-mode effect validation". The log confirmed re-execution (`Re-running method Student.Enroll to validate effects`) across all eleven tests, and nothing was flagged. A re-run with a fresh uuid would construct a second `CourseAttempt` and orphan the first. The author cannot tell from the docs whether validation does not compare what the warning implies, or re-execution reuses the first run's effects. Repeat of Reboot Air 5 (reboot-air-05).

**Expected.** State what effect validation compares, and give the recommended id strategy for "a transaction creates a child actor" (a counter on the parent, as `Institution` does for student ids and diploma numbers? `uuid7` as `stdlib-ordered-map.md` suggests for keys?).

**Repro.** Not recorded.

**Where in the skills.** `python/references/servicer-writer.md`, `python/references/servicer-transaction.md`, `python/references/state-collections.md` (which itself shows `uuid4()` in a constructor).

**Checked at 1.6.0.** `servicer-writer.md` (lines ~18-31) still says bodies re-execute under effect validation; `state-collections.md` (lines ~178-277) still shows `uuid4()` allocated in constructors. No text states what validation compares or recommends an id strategy for transaction-created children.
