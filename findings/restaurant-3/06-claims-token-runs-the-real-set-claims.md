---
id: restaurant-3-06
project: restaurant-3
source: "restaurant-3/FINDINGS.md § Things that worked, item 2"
reboot_version: 1.6.0
severity: green
target: positive
names:
  - python/references/testing-harness.md
tags: [pattern, testing, auth]
cluster: ""
duplicate_of: restaurant-app-3-17
still_applies: unknown
status: Open
resolved_by: ""
---
# `make_valid_oauth_access_token(claims=...)` runs the real `set_claims`

**What happened.** The custom sign-in step mints a token with `email`, `email_verified` and `name`; the roster's `register` ran through the real `set_claims`, no `_authenticated` call needed.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** `python/references/testing-harness.md`, as described.
