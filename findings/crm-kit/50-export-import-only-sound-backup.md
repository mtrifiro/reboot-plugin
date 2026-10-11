---
id: crm-kit-50
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §7"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/api-schema-evolution.md
  - python/references/lifecycle-reboot-cloud.md
  - inspect/SKILL.md
tags: [operations, negative-space]
cluster: "4.1"
duplicate_of: reboot-crm-61
still_applies: yes
status: Resolved
resolved_by: "python/references/lifecycle-backup-restore.md § Do this; python/references/lifecycle-backup-restore.md § Limits"
---

# rbt export / rbt import is the only sound backup before an expunge, and no skill documents it

**What happened.** Before any expunge you'd regret: `rbt export --application-url=<url> --directory=<dir>`; after the fresh boot, `rbt import --application-url=<url> --directory=<dir>`, then boot again. Import matches fields by **name** and refuses unknown ones, so a backup from before a removed or renamed field needs rewriting (renumbered tags need nothing). It overwrites and deletes nothing: restore only into an empty book. A `SortedMap` emptied before export comes back unreadable ("Failed to find column family ... SortedMapEntry"). Idempotency keys survive, so let `initialize` run over the restored data.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** Now partly documented: `api-schema-evolution.md` § Limits (~146) and `lifecycle-reboot-cloud.md` § Limits (~111) say export before and import after can carry data across an expunge, matching by name; no recipe, nothing on restoring only into an empty store, idempotency keys surviving, or the `SortedMapEntry` failure (grep `column family`).
