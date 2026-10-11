---
id: student-sor-08
project: student-sor
source: "student-sor/reboot-findings.md §4c"
reboot_version: 1.5.0
severity: unrated
target: plugin
names:
  - python/references/lifecycle-initialize-hook.md
tags: [cost, seeding, pattern]
cluster: "D"
still_applies: unknown
status: Resolved
resolved_by: "python/references/lifecycle-seeding.md § Scales as"
---

# Measured seed cost after the redesign

**What happened.** Stage 4, 1,760 students with summary-only history and batched roster rows: about ten students a minute sequentially, roughly forty minutes. With one `CourseAttempt` actor per past attempt it was six seconds a student; with a roster transaction per term it was ten. Sequential, effect validation disabled: 193 `admit_student` calls at about one per second, then about six seconds per `import_history` (ten to fifteen nested creates plus one to four roster batches and one index upsert), then thirty-eight petitions and forty-two graduation applications with their decisions. About fifteen minutes end to end on an M-series laptop. Restarting mid-seed resumed correctly through the idempotency aliases, which the author calls a real strength worth advertising.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Candidate numbers for a cost/benchmarking reference and for seeding guidance (proposal tasks C and D).

**Checked at 1.6.0.** No reference carries these numbers or the resume-via-aliases strength note; `python/references/lifecycle-initialize-hook.md` has not been checked for alias-resume language beyond its idempotency-key paragraph (~line 80).
