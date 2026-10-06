---
id: crm-kit-41
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §6"
reboot_version: 1.6.0
severity: unrated
target: bdd
names:
  - python/references/testing-features.md
tags: [testing]
cluster: "4.1"
duplicate_of: reboot-crm-06
still_applies: no
status: Resolved
resolved_by: "python/references/testing-features.md § Never"
---

# BDD: a saved value is bare in a property and quoted only as a state id

**What happened.** `scope_id=<acme id>` recalls the value; `of "<acme id>"` is the state-id form. Quoted in a property it is literal text, and the call aborts `StateNotConstructed` two types away.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `python/references/testing-features.md` § Never (first bullet).
