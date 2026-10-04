---
id: cineloop-23
project: cineloop
source: "cineloop/reboot-findings.md §14 (Part 3)"
reboot_version: 1.4.1
severity: unrated
target: positive
names:
  - python/references/testing-external-context.md
  - python/references/testing-harness.md
tags: [testing, auth]
cluster: "E"
still_applies: unknown
status: Resolved
resolved_by: "python/references/testing-harness.md § Do this"
---

# The test harness runs the real authorizers

**What happened.** `create_external_context_as(name, user_id)` gives a test a genuinely verified identity, so tests exercise the production `authorizer()`. Two tests exist only because of that (`test_orders_are_private`, `test_a_patron_cannot_release_someone_elses_seat`) and would be vacuous under a permissive test authorizer. App-internal calls are built with `create_external_context(name=..., app_internal=True)`, which is how `test_sweep_commits_the_release_for_every_viewer` drives the scheduled sweep directly instead of waiting two real minutes.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Positive pattern about the harness.
