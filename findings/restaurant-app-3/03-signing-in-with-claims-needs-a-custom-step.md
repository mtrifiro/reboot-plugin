---
id: restaurant-app-3-03
project: restaurant-app-3
source: "restaurant-app-3/FINDINGS.md § reboot.bdd, item 2"
reboot_version: 1.6.0
severity: yellow
target: bdd
names:
  - python/references/testing-features.md
  - python/references/testing-harness.md
tags: [testing, auth, negative-space]
cluster: ""
still_applies: yes
status: Resolved
resolved_by: "python/references/testing-features.md § Do this"
---
# Signing in with claims needs a custom step; the built-in mints a token with no claims

**What happened.** Any app that keys its roster by email needs scenario users who carry an email. The built-in `"ben" is an authenticated user` mints a token with no claims, so this build wrote a custom step around `world.rbt.make_valid_oauth_access_token(user_id=..., claims={...})`, found by reading `reboot/bdd/steps.py`. It worked and ran the real `set_claims`.

**Expected.** A built-in step: `Given "ben" is an authenticated user with \`email="ben@crudo.test"\` and \`email_verified=true\``. `testing-harness.md` (line ~135) shows the token with claims for a Python test; `testing-features.md` lists no Gherkin step that carries them.

**Repro.** Key a roster by the `email` claim; sign a scenario user in with the built-in step; the roster lookup finds nothing.

**Where in the skills.** `python/references/testing-features.md` (built-in steps); `python/references/testing-harness.md`.

**Resolution (2026-10-10).** `testing-features.md` says the built-in sign-in step mints a token with no claims and shows that a token with claims is a custom step over `make_valid_oauth_access_token`; `auth-roles.md` carries the step in a feature file. The built-in step is Reboot's.
