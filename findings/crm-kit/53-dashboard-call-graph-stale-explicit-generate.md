---
id: crm-kit-53
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §7"
reboot_version: 1.6.0
severity: unrated
target: framework
names:
  - dashboard/SKILL.md
tags: [operations]
cluster: "F"
duplicate_of: reboot-crm-38
still_applies: no
status: Resolved
resolved_by: "dashboard/SKILL.md § Known issues"
---

# The dashboard call graph goes stale; an explicit uv run rbt generate clears it

**What happened.** The call graph goes stale, and neither a restart nor dev run's own generate clears it; run an explicit `uv run rbt generate`. A dashboard can also outlive its own port; restart it.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `dashboard/SKILL.md` § Known issues covers stale analysis and a dashboard that outlived its 9871 listener (lines ~134-136).
