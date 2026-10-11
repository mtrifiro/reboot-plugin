---
id: cineloop-07
project: cineloop
source: "cineloop/reboot-findings.md §7 (Part 1)"
reboot_version: 1.4.1
severity: unrated
target: positive
names:
  - python/references/auth-built-in-predicates.md
  - python/references/servicer-authorizer.md
tags: [pattern, auth]
cluster: "E"
still_applies: unknown
status: Open
resolved_by: ""
---

# Let the auth model pick the shape of your data (User as home for per-patron work)

**What happened.** `Application(oauth=...)` auto-constructs one `User` actor per signed-in identity whose state ID is `context.auth.user_id`. Consequences: `User` is the natural home for anything per-patron (checkout lives on `User` because it spans three actors: seats sold, order written, order indexed); inside a `User` servicer `self.ref().state_id` is the user ID even on app-internal calls with no bearer token, which is better than `context.auth.user_id` (None on those calls). The framework's default authorizer for `User` (`state_id_is_user_id` OR `is_app_internal`) is exactly right for 'only you can check out as you'; writing one would have been a downgrade.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Positive pattern; kept as a candidate for a `patterns-*` reference (proposal task E).
