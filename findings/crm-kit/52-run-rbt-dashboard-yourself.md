---
id: crm-kit-52
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §7"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - dashboard/SKILL.md
tags: [operations, contradiction]
cluster: "F"
duplicate_of: reboot-crm-45
still_applies: no
status: Resolved
resolved_by: "dashboard/SKILL.md § dashboard — Start the Reboot Developer Dashboard"
---

# rbt dev run does not manage the dashboard; run rbt dashboard yourself

**What happened.** `rbt dev run` does not manage the dashboard. §11: `dashboard/SKILL.md`'s "`rbt dev run` looks after its own dashboard" is false.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** `dashboard/SKILL.md` (§11).

**Checked at 1.6.0.** `dashboard/SKILL.md` description now says `rbt dev run` does not start a dashboard, it only finds one already serving on `--dashboard-port`.
