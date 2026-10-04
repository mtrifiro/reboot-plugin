---
id: reboot-crm-86
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md A.5"
reboot_version: 1.6.0
severity: yellow
target: primer
names: []
tags: [pattern]
cluster: "8.4"
still_applies: unknown
status: Open
resolved_by: ""
---

# A few files hold several features each

**What happened.** `backend/src/servicers/intelligence.py` (1,648 lines) holds sync, company brief, research templates, signal scan and helpers; `web/src/styles.css` (2,612 lines) is one file every change appends to; `backend/src/servicers/common.py` (1,188 lines, 65 definitions) mixes singleton ids, audience gates, queue item formats, cooldowns and the spend helper. Finding the part a change touches means reading the whole file.

**Expected.** Split `intelligence.py` by concern, CSS beside its components, and `common` into ids, gates, research-queue items and pacing; best done with the next expunge.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.
