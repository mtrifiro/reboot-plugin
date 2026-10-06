---
id: agentic-demo-01
project: agentic-demo
source: "v 1.4.1 Reboot/Archive/agentic-demo/docs/reboot-learnings.md §2"
reboot_version: 1.4.0
severity: unrated
target: plugin
names:
  - web-app/SKILL.md
  - python/references/testing-harness.md
tags: [auth, testing, negative-space]
cluster: "4.2"
duplicate_of: theater-chain-04
still_applies: no
status: Resolved
resolved_by: "build/SKILL.md § Step 4 — Authorizers"
---

# The test harness enforces production authorization; rbt dev only warns, so "auth later" breaks the first test run

**What happened.** The web-app skill's recommended sequence was "omit `authorizer()` early; `rbt dev` allows with a 60-second warning". Following it, the whole first test run failed with `aborted with 'PermissionDenied': You are not authorized to call '...Create'`, because `Reboot()`/`rbt.up()` runs production-mode authorization. The testing references explain impersonation, but nothing in the build flow says the auth deferral ends the moment you write tests. For this anonymous demo the correct posture was an explicit `allow()` on every servicer.

**Expected.** One line in web-app's Step 12 (write tests): an app still in the no-authorizer dev posture must add its real authorizers first, or the tests fail on every constructor.

**Repro.** Not recorded beyond the description: build servicers without `authorizer()`, then run a harness test that calls a constructor.

**Where in the skills.** `web-app/SKILL.md` (auth sequence, Step 12).

**Checked at 1.6.0.** `build/SKILL.md` § Step 4 — Authorizers now says to write a real `authorizer()` on every servicer before any test, because `rbt dev` only logs `*** <Type>.<Method> IS MISSING AUTHORIZATION ***` while the `Reboot()` harness, `rbt serve` and Reboot Cloud deny with `PermissionDenied`; `web-app/SKILL.md` § Auth in Web Apps defers to that step. Same gap as theater-chain-04. agentic-demo's learnings file repeats returns-desk's text for this section (it is the same file with §11 added); see returns-desk-01.
