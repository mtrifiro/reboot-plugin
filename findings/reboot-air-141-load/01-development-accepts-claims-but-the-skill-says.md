---
id: reboot-air-141-load-01
project: reboot-air-141-load
source: "reboot-air/REBOOT_LOAD_TEST_FINDINGS.md Finding 1"
reboot_version: 1.4.1
severity: green
target: plugin
names:
  - web-app/SKILL.md
tags: [auth, negative-space]
cluster: "4.1"
still_applies: yes
status: Open
resolved_by: ""
---

# Development accepts claims= but the skill says it does not

**What happened.** `web-app/SKILL.md` documents OAuth providers as a table of required arguments followed by "The registered providers (everything but `Development` and `Anonymous`) also take `scopes=`, `claims=`, and `store_tokens=`." Read plainly, `Development()` cannot take `claims=`. The author spent an afternoon confirming (consistent with the docs) that the dev provider delivers no identity: a `set_claims` override was never called and `User` state stayed empty. The wrong conclusion produced a wrong feature, a booking page asking the user to type the name and email of the account they had just signed in with, rejected twice; the user then pointed out the name and email are visible on the login screen, which sent the author to the installed source. `Development.__init__` takes `claims: Optional[Sequence[str] | Mapping[str, str]] = None`, `_AVAILABLE_CLAIMS` is email, email_verified, name, and a comment in `exchange_code` states the intent ("so that claims-consuming application code can be exercised in local development"). `dev=Development(claims=["email", "name"])` makes `set_claims` fire with `{'email': 'alice@example.com', 'name': 'Alice'}`. Two defects: the table is wrong; and without `claims=` the app sees an opaque `dev-{hash}` only, `set_claims` is never called, and there is no error, warning, or log line. Reboot warns for sixty seconds about a missing `authorizer()` but says nothing about a servicer overriding `set_claims` under a provider configured with no claims. Source severity: low.

**Expected.** Fix the table ("everything but `Anonymous`", list `claims=` on `Development`) and add "without `claims=`, the app receives only an opaque user id and `set_claims` is never called." Framework suggestions: default `Development()` to `claims=["email", "name"]`; warn at startup when a servicer overrides `set_claims` but the provider requests no claims.

**Repro.** Not recorded.

**Where in the skills.** `web-app/SKILL.md`, OAuth provider table. Duplicate of `reboot-air-141-20`.

**Checked at 1.6.0.** Still present. `web-app/SKILL.md:127,134-135` still lists `Development()` with no arguments and excludes it from `claims=`.
