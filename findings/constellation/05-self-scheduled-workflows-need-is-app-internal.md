---
id: constellation-05
project: constellation
source: "v 1.4.1 Reboot/constellation/docs/reboot-learnings.md §2026-08-16 — initial build"
reboot_version: 1.4.0
severity: unrated
target: positive
names:
  - python/references/auth-built-in-predicates.md
tags: [auth, pattern]
cluster: "E"
duplicate_of: cineloop-08
still_applies: no
status: Resolved
resolved_by: "python/references/auth-built-in-predicates.md § Self-scheduled workflows need `is_app_internal`"
---

# Self-scheduled workflows need is_app_internal in the rule

**What happened.** `Video.create` schedules `import_video` on itself, and the workflow then calls `Graph.recompute_edges`. Both run app-internally with no bearer token, so a user-only rule deadlocks the pipeline. The canonical shape for a user-facing actor with background work is `allow_if(any=[has_verified_token, is_app_internal])`.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `python/references/auth-built-in-predicates.md` § Self-scheduled workflows need `is_app_internal` shows the WRONG owner-only rule and the RIGHT `any=[state_id_is_user_id, is_app_internal]`, calling it the canonical rule for user-owned actors with background work.
