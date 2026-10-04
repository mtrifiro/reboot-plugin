---
id: cineloop-19
project: cineloop
source: "cineloop/reboot-findings.md Part 2 §F"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/servicer-authorizer.md
  - python/references/auth-built-in-predicates.md
tags: [negative-space, auth]
cluster: "4.1"
still_applies: yes
status: Resolved
resolved_by: "python/references/servicer-authorizer.md § Do this"
---

# Give authorizer() an app-internal call-paths checklist

**What happened.** `auth-built-in-predicates.md` covers self-scheduled workflows needing `is_app_internal`, but the app had three tokenless paths, only one a workflow. The missing ones, `initialize`-hook seeding and a `Transaction` on actor A calling a `Writer` on actor B, are just as common, and both fail late rather than at startup.

**Expected.** Add to `servicer-authorizer.md` a checklist before writing any authorizer: (1) does `initialize` call this servicer (`InitializeContext` is app-internal, it identifies as the application)? (2) does anything `schedule()` a method on this actor? (3) does another servicer call this one from a `Transaction` or `Writer`? Any yes means the rule needs `is_app_internal` in an `any=[...]`; none fail at startup, they fail the first time the path runs.

**Repro.** Not recorded.

**Where in the skills.** `python/references/servicer-authorizer.md`.

**Checked at 1.6.0.** `python/references/auth-built-in-predicates.md` lines 92-120 cover only 'Self-Scheduled Workflows Need `is_app_internal`'; `servicer-authorizer.md` has no call-path checklist and no mention of `initialize` or transaction-to-writer paths.
