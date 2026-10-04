---
id: student-sor-05
project: student-sor
source: "student-sor/reboot-findings.md §4b"
reboot_version: 1.5.0
severity: unrated
target: plugin
names:
  - python/references/servicer-transaction.md
  - python/references/lifecycle-initialize-hook.md
tags: [negative-space, cost, seeding]
cluster: "C"
still_applies: yes
status: Open
resolved_by: ""
---

# Twelve concurrent bulk-import transactions stalled indefinitely

**What happened.** With `import_history` running for twelve students at once (`asyncio.Semaphore(12)` inside `initialize`), every student was admitted and then nothing else happened: after eight minutes there were zero `CourseAttempt` actors, the processes sat at 0-2% CPU, and the log showed no error, retry or timeout. Each transaction touched its own `Student`, created several `CourseAttempt`s, read a handful of `Course` actors, then wrote the shared `Term` and `Institution` actors. Sequential imports of the same plans complete in five to seven seconds each. The author removed the in-transaction reads (course metadata passed in), fixed the order in which shared actors are touched, and ran imports one at a time. Not verified whether the stall was a lock cycle or something else, because each attempt costs a full expunge and a fifteen-minute seed.

**Expected.** Document how concurrent transactions that overlap on actors are scheduled, whether a wait-for cycle is detected (and how it surfaces), and a recommended pattern for bulk loads that fan out over shared actors. A log line when a transaction has waited on a lock for more than a few seconds would have pointed at the cause.

**Repro.** Not recorded.

**Where in the skills.** `python/references/servicer-transaction.md`.

**Checked at 1.6.0.** `python/references/servicer-transaction.md` (lines ~21-24, 148) mentions concurrent callers queueing and `asyncio.gather` for sub-calls but says nothing on overlapping-actor scheduling, deadlock detection or bulk-load patterns.
