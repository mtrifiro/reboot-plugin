---
id: reboot-crm-92
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md A.11"
reboot_version: 1.6.0
severity: green
target: primer
names: []
tags: [pattern]
cluster: "8.4"
still_applies: unknown
status: Open
resolved_by: ""
---

# Comments carry history that belongs in commits

**What happened.** Incident-and-date comments explain why in a way nothing else does and should stay, but some functions carry thirty lines of history, some now stale (Poggio), and every read pays for it.

**Expected.** Keep the why at the point of use; move the narrative to the commit message or a finding.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.
