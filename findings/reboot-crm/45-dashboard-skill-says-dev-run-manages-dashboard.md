---
id: reboot-crm-45
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P3.9"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - dashboard/SKILL.md
tags: [contradiction, operations]
cluster: "F"
still_applies: yes
status: Open
resolved_by: ""
---

# The dashboard skill says rbt dev run looks after its own dashboard; rbt dev run says it does not

**What happened.** `skills/dashboard/SKILL.md` states twice that the skill is "not for running an app; `rbt dev run` manages its dashboard itself once the app exists". `rbt dev run --help` says `--dashboard-port` is the port on which the developer dashboard, "started separately with `rbt dashboard`", is serving. A `rbt dev run` with nothing on 9871 prints an API URL, an MCP URL and an inspect URL, no dashboard URL, and 9871 stays empty. Acting on the skill's wording costs a round trip: the app is up, the dashboard tab says offline.

**Expected.** Correct `dashboard/SKILL.md`; a one-line doc fix.

**Repro.** Run `rbt dev run` with nothing on port 9871.

**Where in the skills.** `dashboard/SKILL.md` (description and line ~32). Also listed in run skill coverage (cluster F).

**Checked at 1.6.0.** `dashboard/SKILL.md` line 3 (description) and line 32 still say `rbt dev run` looks after its own dashboard.
