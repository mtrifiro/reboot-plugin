---
id: crm-kit-03
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §1"
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

# Patch B: rbt generate dies with ENOBUFS once the app grows; a `maxBuffer` patch removes it

**What happened.** `rbt generate` prints `protoc-gen-es-with-deps: spawnSync /bin/sh ENOBUFS`, and `rbt dev run` sits at "Protoc compilation failed ... waiting for modification". The Python side generates and `mypy` passes, so it looks like an API problem; it is not. Cause: `reboot/protoc_gen_es_with_deps.cjs` runs `execSync` with Node's default 1 MiB buffer; seen when one `*_pb.ts` reached 1.03 MB. Fix: the same idempotent script rewrites `execSync("protoc-gen-es", {` to add `maxBuffer: 256 * 1024 * 1024,`. Needed on every platform once the app grows; reverted by any reinstall like Patch A.

**Expected.** Not recorded beyond the local patch.

**Repro.** Not recorded.

**Where in the skills.** Not named by the source.

**Checked at 1.6.0.** No `ENOBUFS` or `maxBuffer` anywhere under `skills/` (grep).

**Resolution (2026-10-10).** Rows in `lifecycle-dev-loop.md` § Errors you will see: `spawnSync /bin/sh ENOBUFS` with the venv `maxBuffer` patch and the restart; a half-edited module after one of two saves (undeclared errors retry with backoff); the stale effect-validation docs link.
