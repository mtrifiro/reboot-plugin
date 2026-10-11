---
id: restaurant-app-3-17
project: restaurant-app-3
source: "restaurant-app-3/FINDINGS.md § Things that worked, item 5"
reboot_version: 1.6.0
severity: green
target: positive
names:
  - python/references/testing-harness.md
tags: [pattern, testing, auth]
cluster: ""
still_applies: unknown
status: Open
resolved_by: ""
---
# Claims through the harness ran the real `set_claims`

**What happened.** `make_valid_oauth_access_token(claims=...)` ran the real `set_claims` path in scenarios, so the email-keyed roster was tested as deployed. It only needs a built-in Gherkin step (restaurant-app-3-03).

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** `python/references/testing-harness.md`.
