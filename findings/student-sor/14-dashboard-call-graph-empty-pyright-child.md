---
id: student-sor-14
project: student-sor
source: "student-sor/reboot-findings.md §8b"
reboot_version: 1.5.0
severity: unrated
target: framework
names:
  - dashboard/SKILL.md
tags: [operations]
cluster: "F"
duplicate_of: reboot-air-150-12
still_applies: yes
status: Resolved
resolved_by: "dashboard/SKILL.md § Known issues"
---

# Dashboard Call Graph empty until the Pyright child is killed

**What happened.** On this project too the Call Graph rendered every state type with no edges. One `node .../pyright/dist/langserver.index.js` child from the project's `.venv` was still alive after the analysis; killing it let the result publish ("102 calls between 10 state types"). Same as student-system-10. The full write-up with a repro is `../student-system/docs/reboot-dashboard-call-graph-bug.md`.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** `dashboard/SKILL.md` (no known-issues section).

**Checked at 1.6.0.** `dashboard/SKILL.md` has no mention of pyright, `langserver` or the Call Graph.
