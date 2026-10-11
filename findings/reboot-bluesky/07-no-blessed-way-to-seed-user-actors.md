---
id: reboot-bluesky-07
project: reboot-bluesky
source: "REBOOT_FINDINGS.md §7"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/patterns-common-gotchas.md
  - python/references/testing-harness.md
tags: [seeding, auth, version-drift]
cluster: "C"
still_applies: unknown
status: Resolved
resolved_by: "python/references/lifecycle-seeding.md § Limits"
---

# No blessed path for seeding User-type actors

**What happened.** Seeding test data for an `oauth=` app means constructing `User` actors for identities that never signed in. The only mechanism is the semi-private `UserServicer._authenticated(context, state_id)`, which exists only on the servicer class at runtime, while the 1.4.0 migration note says it lives on the state type and the servicer (mypy agrees with runtime: `User._authenticated` does not exist).

**Expected.** An official seeding/impersonation API (e.g. `Application.seed_user(...)` or a `rbt dev seed` hook), and fix the docs/type divergence.

**Repro.** Not recorded.

**Where in the skills.** Not recorded; auth references and the 1.4.0 migration note.

**Checked at 1.6.0.** python/references/testing-harness.md:216 and patterns-common-gotchas.md:285 cover impersonation in tests (token minting constructs `User`), but I found no guidance for seeding `User` actors from `initialize`. Left unknown.
