---
id: constellation-04
project: constellation
source: "v 1.4.1 Reboot/constellation/docs/reboot-learnings.md §2026-08-16 — initial build"
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

# The test harness enforces authorizers even when rbt dev would not

**What happened.** With no `authorizer()` defined, `rbt dev` allows calls and logs a warning, but `Reboot()` unit tests run production-mode auth and every external call fails with `PermissionDenied`. Fix: write the real rules from day one (the app has `oauth=` identity, so `allow_if(any=[has_verified_token, is_app_internal])`) and impersonate in tests with `create_external_context_as(name, user_id)`.

**Expected.** Not recorded.

**Repro.** Boot a servicer without `authorizer()` in a harness test and call any method from `create_external_context(...)`.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `python/references/servicer-authorizer.md` § When to write it tabulates the modes (dev allowed with warning; harness denied as in production); `auth-allow-deny.md` and `api-methods.md` mention `rbt.create_external_context_as(name, user_id)` for tests.
