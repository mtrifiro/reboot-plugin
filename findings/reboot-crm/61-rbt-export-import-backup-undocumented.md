---
id: reboot-crm-61
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P3.24"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - inspect/SKILL.md
  - python/references/lifecycle-reboot-cloud.md
  - python/references/api-schema-evolution.md
tags: [negative-space, operations, index-gap, seeding]
cluster: "4.1"
still_applies: yes
status: Resolved
resolved_by: "python/references/lifecycle-backup-restore.md § Do this; python/references/lifecycle-backup-restore.md § Limits"
---

# rbt export and rbt import exist and are the only sound backup; no skill says so, and --config does not expand for them

**What happened.** Every breaking API change costs an expunge and an expunge deletes the data. Nothing in the skills offers a way to keep it: `inspect/SKILL.md` has one clause ("Both flags match `rbt export` / `rbt import`") pointing at `lifecycle-reboot-cloud.md`, which says nothing about either. Reading the package (`reboot/cli/commands/export_import.py`, `reboot/admin/export_import_servicer.py`, `reboot/aio/state_managers.py`) shows a complete facility: JSON lines per server for every actor's state, task, idempotency record and sorted-map entry; import parses each line against the running application's types, overwrites on collision, deletes nothing, re-dispatches every incomplete task; on Cloud the Cloud API key is accepted as the admin credential. Undocumented facts: (1) lines go out and come back by field name and the import refuses unknown names (`ignore_unknown_fields` off); (2) idempotency keys survive an expunge (seeded from the application id), so an action-only alias is found done after a restore even though its task is gone; (3) the export is not a point-in-time snapshot (servers export concurrently with writers running); (4) an emptied `SortedMap` imports as a bare actor and every `Range` fails with "Failed to find column family for state type 'rbt.std.collections.v1.SortedMapEntry'" until some map is constructed (the import constructs nothing); (5) tag numbers do not travel but state types and ids do (a package move changes every ref, since the prefix is a hash of the full type name); (6) the import places each line by the running application's placement client, so a backup restores into a different `--size`; (7) a refused line says only "Failed to parse import item, is it possible the types being imported are not backwards compatible?" after the import has stopped part-way and whatever was written stays. Also `rbt export --config=prod` ignores an `export:prod --application-url=...` `.rbtrc` line (argument parsing still asks for `--application-url`) while a plain `export --application-url=...` line is honoured.

**Expected.** Fixes proposed: have the import create the entry column family for any imported `SortedMap` actor (framework); add a `backup-restore` reference under the python skill's lifecycle section (the two commands, line format, the facts above, the recipe: export; expunge; boot; import; boot again); a line in `api-schema-evolution.md`'s "Recovering From a Rejected Deploy" that expunge is not data loss if you export first; make `--config` expand for `export`/`import` or say in help it does not. Recommendation: the reference first.

**Repro.** Not recorded beyond the project's `tests/restore_roundtrip_test.py` for the SortedMap case.

**Where in the skills.** `python/references/lifecycle-reboot-cloud.md`, `python/references/api-schema-evolution.md`, `inspect/SKILL.md`; no `backup-restore` reference exists.

**Checked at 1.6.0.** `inspect/SKILL.md` line 58 is the only mention of `rbt export`/`rbt import` under `skills/` (grep); no backup/restore reference exists.
