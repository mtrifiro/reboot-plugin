---
id: reboot-crm-84
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md A.3"
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

# Names have drifted from what they mean

**What happened.** Each cost a careful read: the Intelligence panel lives in `web/src/components/Poggio.tsx`; `templates_off()` means "this teammate is on simple research"; `Account.note_intelligence` takes `poggio_status` for whatever the research status is; `ACCOUNT_BRIEF` aliases `ACCOUNT_ITEM`; `TeamState.templates_for` is stored and never read. Status: names outside `api/` fixed 2026-10-04; names inside `api/` wait for the next expunge (reboot-crm-85).

**Expected.** Rename everything outside `api/` now since it costs nothing; names inside `api/` wait for A.4.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.
