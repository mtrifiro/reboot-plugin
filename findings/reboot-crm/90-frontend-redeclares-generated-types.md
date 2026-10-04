---
id: reboot-crm-90
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md A.9"
reboot_version: 1.6.0
severity: yellow
target: primer
names: []
tags: [frontend, pattern]
cluster: "8.4"
still_applies: unknown
status: Open
resolved_by: ""
---

# The frontend re-declares the generated types by hand

**What happened.** Components declare interfaces of their own (`PageView`, `ResearchView`, `ScanView`, `SignalItem`) that duplicate the generated types field for field. They can drift from the API silently and an agent must check both to know which is true.

**Expected.** Import the generated types (camelCased) instead.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.
