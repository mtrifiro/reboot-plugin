---
id: reboot-crm-11
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P1.5"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - python/references/api-schema-evolution.md
tags: [negative-space, error-text]
cluster: "4.1"
still_applies: yes
status: Open
resolved_by: ""
---

# A method's description= is part of the frozen schema (second sighting)

**What happened.** Rewording only the `description=` of the existing `Leads.leads` reader (no field or kind change) made the app refuse to start against its persisted state; restoring the exact wording fixed it. `api-schema-evolution.md` lists field and method-kind rules but never says descriptions are compared. The source recommends merging with reboot-crm-10 and keeping this repro as the cleaner one (only the description changed).

**Expected.** Either descriptions are free to change (they are documentation, and MCP-facing ones can be `mcp=None`), or the reference says they are frozen and the error names the field.

**Repro.** Reword only a method's `description=` and restart against persisted state.

**Where in the skills.** `python/references/api-schema-evolution.md`.

**Checked at 1.6.0.** Same as reboot-crm-10: no description row or warning in `python/references/api-schema-evolution.md`.
