---
id: cineloop-08
project: cineloop
source: "cineloop/reboot-findings.md §8 (Part 1)"
reboot_version: 1.4.1
severity: unrated
target: positive
names:
  - python/references/auth-built-in-predicates.md
  - python/references/servicer-authorizer.md
  - python/references/lifecycle-initialize-hook.md
tags: [auth, pattern]
cluster: "E"
still_applies: unknown
status: Open
resolved_by: ""
---

# is_app_internal is load-bearing in more places than expected

**What happened.** Three call paths arrive with no bearer token: (1) `initialize` seeding the catalog on boot (`InitializeContext` sets a `caller_id` matching the application, so it is app-internal; worth knowing before reaching for `allow()`); (2) the `sweep` the showing schedules on itself; (3) the `confirm` that `User.checkout` issues from inside its transaction. Hence every servicer uses `allow_if(any=[<user rule>, is_app_internal])`. Getting this wrong does not fail at startup; it fails two minutes later when the first hold tries to expire.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Positive pattern; kept as a candidate for a `patterns-*` reference (proposal task E). The plugin gap is item 19 (call-path checklist).
