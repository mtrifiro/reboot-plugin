---
id: reboot-crm-39
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P3.6"
reboot_version: 1.6.0
severity: yellow
target: framework
names:
  - python/references/lifecycle-rbtrc.md
tags: [operations, negative-space]
cluster: "F"
still_applies: unknown
status: Open
resolved_by: ""
---

# dev run --watch did not pick up a change under backend/src/

**What happened.** `.rbtrc` carried `dev run --watch=backend/src/**/*.py`. An edit to `backend/src/servicers/leads.py` did not restart the application: the log held a single "Pipeline ready" from the original boot and a failing task kept retrying against code already fixed, reading as "the fix did not work". Edits under `backend/api/` (from `rbt generate`) did restart it repeatedly. Killing the processes and restarting picked the change up. Not reproduced deliberately; trigger unclear (possibly the glob, possibly the watcher stopping after an earlier reload).

**Expected.** Fixes proposed: log the resolved glob and file count at startup and each restart trigger's path; log when the watcher dies; audit the glob semantics. Recommendation: observability before a fix.

**Repro.** Not reproduced deliberately.

**Where in the skills.** `python/references/lifecycle-rbtrc.md` (lines ~40-42 show the same `--watch` globs).

**Checked at 1.6.0.** `lifecycle-rbtrc.md` still recommends the `backend/src/**/*.py` watch glob; nothing documents the failure.
