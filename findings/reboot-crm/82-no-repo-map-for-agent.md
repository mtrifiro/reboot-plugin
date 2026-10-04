---
id: reboot-crm-82
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md A.1"
reboot_version: 1.6.0
severity: red
target: primer
names: []
tags: [index-gap, operations]
cluster: "4.6"
still_applies: unknown
status: Open
resolved_by: ""
---

# No map of the repo for an agent: every session rebuilds the layout by grepping

**What happened.** Every session starts by rediscovering which test module runs which feature file, where singletons are created, that generated code is not tracked, that `scripts/suite.sh` runs the suite, and that the backup must precede a deploy. `docs/` held twenty overlapping files and nothing said which was current; earlier write-ups were folded into the findings document and deleted on 2026-10-04. Status: done 2026-10-04. The change: a root `CLAUDE.md` with where each concept lives, how to run/test/deploy, which doc is authoritative, and the rules that cost the most (backup alone before deploy; no codegen during a suite; method descriptions are schema). Estimated worth 10-20 minutes a task.

**Expected.** Not recorded beyond the change made in the app.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.
