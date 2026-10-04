---
id: student-sor-11
project: student-sor
source: "student-sor/reboot-findings.md §6"
reboot_version: 1.5.0
severity: unrated
target: framework
names:
  - python/references/lifecycle-initialize-hook.md
tags: [seeding, operations, error-text]
cluster: "C"
still_applies: yes
status: Open
resolved_by: ""
---

# initialize retries a failing seed forever with backoff, without surfacing the failure to rbt dev run

**What happened.** A prerequisite-ordering bug in the seeder made `add_course` abort. The log shows `initialize for application ... failed with AddCourseAborted ... will retry after backoff`, and the application kept restarting `initialize` every few seconds. `rbt dev run` itself reported nothing. Same shape as student-system-02 and reboot-air-03.

**Expected.** A failing `initialize` should be loud in the CLI output, and a bounded number of retries would make the failure obvious.

**Repro.** Not recorded.

**Where in the skills.** `python/references/lifecycle-initialize-hook.md` (no mention of retry-on-failure).

**Checked at 1.6.0.** `python/references/lifecycle-initialize-hook.md` has no text on initialize failure retrying with backoff.
