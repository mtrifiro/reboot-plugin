---
id: restaurant-3-03
project: restaurant-3
source: "restaurant-3/FINDINGS.md § reboot.bdd, item 2"
reboot_version: 1.6.0
severity: yellow
target: bdd
names:
  - python/references/testing-features.md
tags: [negative-space, testing, error-text]
cluster: ""
still_applies: yes
status: Open
resolved_by: ""
---
# A custom step registered only with `@given` falls to a catch-all under `When`

**What happened.** `Given "ben" signs in with the verified email "..."` worked; the same line after a `When` (as `And`) failed with `ValueError: Almost: each clause goes in backticks, e.g. `amount=50``, because a built-in `@when` catch-all matched the ` with ` in the text. The catch-all is the one reboot-crm-21 met through web-app text; here the cause is the missing `@when` registration.

**Expected.** "Step definition is not found" naming the step, or a hint that custom steps need both `@given` and `@when` when an `And` may follow a `When`.

**Repro.** A `@given(parsers.parse('"{user}" signs in with the verified email "{email}"'))` step used under `When`.

**Where in the skills.** `python/references/testing-features.md` ("Custom steps are plain Reboot code") shows only `@when`/`@then`; nothing says to register both keywords.
