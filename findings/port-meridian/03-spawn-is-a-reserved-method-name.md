---
id: port-meridian-03
project: port-meridian
source: "v 1.4.1 Reboot/port-meridian/docs/reboot-learnings 04.md §3"
reboot_version: 1.4.0
severity: unrated
target: plugin
names:
  - python/references/api-methods.md
tags: [negative-space, error-text]
cluster: "4.1"
duplicate_of: reboot-air-141-13
still_applies: no
status: Resolved
resolved_by: "python/references/rpc-refs.md § Limits"
---

# spawn is a reserved method name, and only rbt generate says so

**What happened.** `spawn` is a reserved method name in pydantic APIs (`Spawn is reserved`); the error surfaces only at `rbt generate` time.

**Expected.** Not recorded.

**Repro.** Declare a method named `spawn` and run `rbt generate`.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `python/references/rpc-refs.md` § Limits: "Method names `read`, `write`, `delete`, `state`, `schedule`, `spawn` are rejected by codegen"; `api-methods.md` also notes names reserved by the ref API.
