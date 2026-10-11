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
status: Resolved
resolved_by: "python/references/lifecycle-dev-loop.md § Errors you will see"
---

# Patch B, maxBuffer: rbt generate fails with ENOBUFS once the API grows

**What happened.** Without Patch B, `rbt generate` fails with `protoc-gen-es-with-deps: spawnSync /bin/sh ENOBUFS` once the API grows. The script adds `maxBuffer: 256 * 1024 * 1024` to the `execSync("protoc-gen-es", {` call in `protoc_gen_es_with_deps.cjs`; both printed lines must end `True`. Reverted by any reinstall.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** No `ENOBUFS` or `maxBuffer` anywhere under `skills/` (grep).

**Resolution (2026-10-10).** Rows in `lifecycle-dev-loop.md` § Errors you will see: `spawnSync /bin/sh ENOBUFS` with the venv `maxBuffer` patch and the restart; a half-edited module after one of two saves (undeclared errors retry with backoff); the stale effect-validation docs link.
