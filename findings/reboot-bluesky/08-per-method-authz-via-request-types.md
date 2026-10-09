---
id: reboot-bluesky-08
project: reboot-bluesky
source: "REBOOT_FINDINGS.md §8"
reboot_version: 1.4.1
severity: unrated
target: framework
names: []
tags: [auth]
cluster: "8.4"
duplicate_of: student-system-06
still_applies: unknown
status: Resolved
resolved_by: "python/references/auth-custom-predicates.md § Never; python/references/servicer-authorizer.md § Never"
---

# Per-method authorization has to be smuggled through request types

**What happened.** `authorizer()` is one rule for all methods, and the escape hatch is dispatching on the request model, which fails for `request=None` methods (they all arrive as `None`). The app invented empty request models (`ProfileRequest`, `MarkDeletedRequest`) purely so the authorizer could tell methods apart.

**Expected.** Pass the method name to predicates, or support per-method rules directly.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.
