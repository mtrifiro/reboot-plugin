---
id: student-sor-07
project: student-sor
source: "student-sor/reboot-findings.md §4b-3"
reboot_version: 1.5.0
severity: unrated
target: framework
names:
  - python/references/servicer-transaction.md
tags: [negative-space, error-text, seeding]
cluster: "8.4"
still_applies: unknown
status: Resolved
resolved_by: "python/references/servicer-transaction.md § Limits"
---

# A transaction's child construct survived while its parent did not (partial commit)

**What happened.** After the concurrent attempt above was reverted and the app restarted, `initialize` failed on every retry with `Institution.AdmitStudentAborted: aborted with 'Unknown': unhandled (in 'sor.v1.Institution.AdmitStudent') aborted with 'StateAlreadyConstructed'`. `rbt inspect` showed 347 `Student` actors but `Institution.next_student_number` = 346 and `student_count` = 346. `admit_student` is a Transaction that increments the counter, then `Student.create`s `S{100000+n}`, then inserts the index row. Exactly one `Student` (S100347) exists whose creating transaction never committed its `Institution` side, so the next admission recomputed the same id and could not construct it. The student's email matched the pending admission, so it was the cancelled/timed-out transaction from the lock-wait period. It looks like a participant commit racing a coordinator abort. The author made `admit_student` probe the next id and adopt an existing `Student` with the same email (or skip a stray one), which is defensive and should not be necessary.

**Expected.** `servicer-transaction.md` says a transaction is all-or-nothing across actors.

**Repro.** `GROWTH_CONCURRENCY = 4` in `backend/src/seed.py` with a fresh `rbt dev expunge`; the tracebacks in student-sor-06 precede it.

**Where in the skills.** `python/references/servicer-transaction.md` (all-or-nothing claim).

**Checked at 1.6.0.** Not checked against skills beyond `servicer-transaction.md`; this is runtime behaviour, no skill text addresses it.
