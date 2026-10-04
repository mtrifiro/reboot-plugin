---
id: showtime-49
project: showtime
source: "2026.08.18 reboot-findings.md Suggested skill improvements, bullet 6"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/rpc-constructor-calls.md
tags: [contradiction, negative-space]
cluster: "4.1"
still_applies: yes
status: Open
resolved_by: ""
---

# rpc-constructor-calls.md says use Service.create for factory-less types, but codegen emits none

**What happened.** `rpc-constructor-calls.md` says 'when the Type has no explicit factory, use `Service.create`' but codegen emits no `create` for factory-less types (showtime-32).

**Expected.** Either codegen emits it, or the reference says factory-less types are created implicitly on first mutator call and there is no `create` to call.

**Repro.** Not recorded.

**Where in the skills.** `rpc-constructor-calls.md`.

**Checked at 1.6.0.** python/references/rpc-constructor-calls.md:53-61 unchanged.
