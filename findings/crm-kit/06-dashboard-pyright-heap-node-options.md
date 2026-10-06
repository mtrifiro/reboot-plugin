---
id: crm-kit-06
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §1"
reboot_version: 1.6.0
severity: unrated
target: framework
names:
  - dashboard/SKILL.md
tags: [operations, cost, error-text]
cluster: "F"
duplicate_of: reboot-crm-22
still_applies: no
status: Resolved
resolved_by: "dashboard/SKILL.md § Known issues"
---

# The dashboard's pyright dies at 4.1 GB on a 14-type app; start it with a larger Node heap

**What happened.** At 14 types and about 180 methods, the dashboard's pyright died at 4.1 GB. The page then says permanently "...generated code that does not exist yet... Run `rbt generate`", which never fixes it. Workaround: start the dashboard as `NODE_OPTIONS="--max-old-space-size=12288" uv run rbt dashboard`.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `dashboard/SKILL.md` § Known issues (line ~132) and `errors.md` list the pyright out-of-heap case (grep `max-old-space-size`).
