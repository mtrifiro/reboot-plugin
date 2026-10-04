---
id: reboot-crm-76
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P4.7"
reboot_version: 1.6.0
severity: green
target: framework
names:
  - inspect/SKILL.md
tags: [operations, error-text]
cluster: "F"
still_applies: no
status: Open
resolved_by: ""
---

# rbt inspect insists on --type=VALUE

**What happened.** `rbt inspect state list --type crm.v1.Intelligence` (a space) fails with "expected --type=VALUE, missing '=VALUE' (did you mean --type=crm.v1.Intelligence)". Every other argparse CLI takes both spellings; the skill's examples used the space form.

**Expected.** Accept the space form as well as `--type=...` (recommendation: do it).

**Repro.** Not recorded.

**Where in the skills.** `inspect/SKILL.md` examples.

**Checked at 1.6.0.** `inspect/SKILL.md` (lines 4, 37, 40) now uses `--type=<full.Type.Name>`, so the skill no longer teaches the rejected spelling; the CLI behaviour itself is unchanged as far as recorded.
