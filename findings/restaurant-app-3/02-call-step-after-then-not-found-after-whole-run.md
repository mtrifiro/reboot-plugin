---
id: restaurant-app-3-02
project: restaurant-app-3
source: "restaurant-app-3/FINDINGS.md § reboot.bdd, item 1"
reboot_version: 1.6.0
severity: yellow
target: bdd
names:
  - python/references/testing-features.md
tags: [testing, error-text]
cluster: ""
still_applies: yes
status: Resolved
resolved_by: "python/references/testing-features.md § Errors you will see"
---
# A built-in call step after `Then` fails as "Step definition is not found", and only after the whole run

**What happened.** Two scenarios wrote `Then …` followed by `And "dani" does a \`send_items\` …` and `And "esi" attempts an \`advance\` …`. Both failed with `StepDefinitionNotFoundError: Step definition is not found: Then ""dani" does a \`send_items\` with ... on \`Check\` of "<rossi>""`, and only after a 7m46s suite run.

**Expected.** The Errors table in `testing-features.md` names `saves the text of`, `clicks` and `fills` as the When-only steps; `does`, `attempts` and `creates` are too. An "Almost:" hint like the one for `eventually has` ("this is a Given/When step; it follows a Then") would make it a one-second fix. The same split was unstated for `saves the text of` in reboot-crm's P4.6 (reboot-crm-75), and plugin-browser-02 reports another bare not-found with no hint.

**Repro.** `Then as "a", \`get\` on the \`X\` for "x" has \`v=1\`` then `And "a" does an \`inc\` on \`X\` of "x"`.

**Where in the skills.** `python/references/testing-features.md`, Errors table (the `Step definition is not found:` row); `reboot/bdd/steps.py` for the hint.

**Resolution (2026-10-10).** The templates' `tests/step_order.py`, imported by `conftest.py`, looks up every step before a scenario runs; a step under a `Then` that matches only an action fails the scenario at once, with the file and line and the fix (move it above the first `Then`, or split the scenario). `feature` Step 2 says a scenario is set-up, actions, then checks, and the Errors table carries the new message. Seen again in a later restaurant-app-3 session (`tests/managing.feature:37`, `tests/kitchen.feature:33`). Projects copied before this change don't have the check.
