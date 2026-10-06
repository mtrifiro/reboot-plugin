---
id: new-crm-02
project: new-crm
source: "new-crm/docs/PATCHES.md §Patch B"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/patterns-common-gotchas.md
tags: [negative-space, error-text, operations]
cluster: "4.4"
duplicate_of: reboot-crm-08
still_applies: yes
status: Open
resolved_by: ""
---

# Patch B, maxBuffer: rbt generate fails with ENOBUFS once the API grows

**What happened.** Without Patch B, `rbt generate` fails with `protoc-gen-es-with-deps: spawnSync /bin/sh ENOBUFS` once the API grows. The script adds `maxBuffer: 256 * 1024 * 1024` to the `execSync("protoc-gen-es", {` call in `protoc_gen_es_with_deps.cjs`; both printed lines must end `True`. Reverted by any reinstall.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** No `ENOBUFS` or `maxBuffer` anywhere under `skills/` (grep).
