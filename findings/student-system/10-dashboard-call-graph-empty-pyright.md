---
id: student-system-10
project: student-system
source: "student-system/reboot-findings.md §10"
reboot_version: 1.5.0
severity: unrated
target: framework
names:
  - dashboard/SKILL.md
tags: [operations]
cluster: "F"
duplicate_of: reboot-air-150-12
still_applies: yes
status: Open
resolved_by: ""
---

# Dashboard Call Graph stays empty forever (orphaned pyright child blocks Pyright.stop())

**What happened.** `rbt dashboard`'s Call Graph shows "0 calls between 9 state types" and "Your application imports generated code that does not exist yet. Run rbt generate" while the generated code exists and its digest matches. Root cause reproduced outside the dashboard: after a 17-second analysis that finds every servicer and call, `Pyright.stop()` blocks forever because the pyright-python wrapper's node child keeps the stdout pipe open and asyncio's `wait()` never returns. One orphaned `node .../langserver.index.js` per iteration. A write-up with a minimal repro script is `docs/reboot-dashboard-call-graph-bug.md` in the source project (same as reboot-air-12). Workaround: `pkill -f langserver.index.js` after the dashboard has been up a few seconds.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** `dashboard/SKILL.md` has no known-issues note for this (see proposal task F).

**Checked at 1.6.0.** `dashboard/SKILL.md` has no mention of pyright, `langserver`, or the Call Graph.
