---
id: theater-chain-04
project: theater-chain
source: "theater-chain/reboot-findings.md §4"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - web-app/SKILL.md
  - python/references/servicer-authorizer.md
  - python/references/auth-custom-predicates.md
  - python/references/testing-harness.md
tags: [contradiction, auth, negative-space, testing]
cluster: "4.2"
still_applies: yes
status: Open
resolved_by: ""
---

# Omit authorizer in early dev and write tests are mutually exclusive

**What happened.** `web-app/SKILL.md` auth-sequence step 1 says to omit `authorizer()` early and treat the 60-second dev warning as a TODO list; step 12 says to write and pass backend tests before handoff. `rbt.up()` runs production authorization, so every unauthorized method is `PermissionDenied` the moment a test touches it; the first test run died on `Chain.Get` before asserting anything. `servicer-authorizer.md` is right and the web-app skill is out of step: for an app wired with `oauth=` (every web app the skill scaffolds, including `Development()`), the guidance there is to write real `allow_if(...)` rules from day one. Two further auth facts the author wants written down: servicer-to-servicer calls are `app_internal` but carry no user identity, so a predicate like `if request is None: <check auth>` denies nested reader calls with a confusing `Unauthenticated`; check `context.app_internal` first, always. `initialize` is app-internal, so seeding through internal-only `create` methods works; in tests the equivalent is `rbt.create_external_context(name=..., app_internal=True)`, worth a named helper (`self.house()` here).

**Expected.** Delete the "omit `authorizer()` early" arm from `web-app/SKILL.md`'s auth sequence, or scope it explicitly to `token_verifier=` apps, matching `servicer-authorizer.md`. Add a note to `auth-custom-predicates.md` that servicer-to-servicer calls are `app_internal` with no user identity, so `context.app_internal` must be checked first.

**Repro.** Not recorded.

**Where in the skills.** `web-app/SKILL.md` (auth sequence, steps 1 and 12) versus `python/references/servicer-authorizer.md`; `python/references/auth-custom-predicates.md`.

**Checked at 1.6.0.** Still present. `web-app/SKILL.md:103-111` still says to omit `authorizer()` early; `python/references/servicer-authorizer.md:60-66` says write rules from day one for `oauth=` apps, so the two disagree. `python/references/auth-built-in-predicates.md:38-48` does not say in-app calls carry no user identity.
