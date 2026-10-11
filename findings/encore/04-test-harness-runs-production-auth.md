---
id: encore-04
project: encore
source: "v 1.4.1 Reboot/encore/docs/reboot-learnings 02.md §4"
reboot_version: 1.4.0
severity: unrated
target: plugin
names:
  - python/references/servicer-authorizer.md
tags: [auth, testing]
cluster: "4.2"
duplicate_of: theater-chain-04
still_applies: no
status: Resolved
resolved_by: "python/references/servicer-authorizer.md § When to write it"
---

# The test harness runs production auth

**What happened.** Known from earlier projects, reconfirmed: `Reboot()` + `rbt.up(...)` enforces authorizers, so an anonymous public demo needs an explicit `def authorizer(self): return allow()` on every servicer or every test fails with PERMISSION_DENIED on the first RPC.

**Expected.** Not recorded.

**Repro.** A servicer with no `authorizer()` called from a harness test.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `python/references/servicer-authorizer.md` § When to write it has a mode table: missing `authorizer()` is allowed with a warning under `rbt dev` but denied (`PermissionDenied`) in the `Reboot()` test harness, as in production.
