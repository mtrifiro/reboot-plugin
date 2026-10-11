---
id: student-sor-10
project: student-sor
source: "student-sor/reboot-findings.md §5"
reboot_version: 1.5.0
severity: unrated
target: framework
names: []
tags: [operations, seeding]
cluster: "8.4"
still_applies: unknown
status: Resolved
resolved_by: "python/references/lifecycle-seeding.md § Limits"
---

# Effect-validation log lines are silenced for five minutes, hiding progress

**What happened.** `Re-running method X to validate effects ... Will silence this message for the next 5 minutes.` is logged once per method and then suppressed. During a long `initialize` that is the only sign of life, so for five minutes the log looks hung.

**Expected.** A periodic summary ("re-ran 412 methods in the last minute") would help; so would a way for `initialize` to report progress.

**Repro.** Not recorded.

**Where in the skills.** Not applicable to a skill unless a seeding reference warns that the log goes quiet.

**Checked at 1.6.0.** No skill mentions this log line (grep for `5 minutes` found nothing relevant).

**Resolution (2026-10-10).** `lifecycle-seeding.md` § Limits: a long seed goes quiet because the `Re-running` line is silenced for five minutes; measure progress from state.
