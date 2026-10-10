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
status: Open
resolved_by: ""
---
# A built-in call step after `Then` fails as "Step definition is not found", and only after the whole run

**What happened.** Two scenarios wrote `Then …` followed by `And "dani" does a \`send_items\` …` and `And "esi" attempts an \`advance\` …`. Both failed with `StepDefinitionNotFoundError: Step definition is not found: Then ""dani" does a \`send_items\` with ... on \`Check\` of "<rossi>""`, and only after a 7m46s suite run.

**Expected.** The Errors table in `testing-features.md` names `saves the text of`, `clicks` and `fills` as the When-only steps; `does`, `attempts` and `creates` are too. An "Almost:" hint like the one for `eventually has` ("this is a Given/When step; it follows a Then") would make it a one-second fix. The same split was unstated for `saves the text of` in reboot-crm's P4.6 (reboot-crm-75), and plugin-browser-02 reports another bare not-found with no hint.

**Repro.** `Then as "a", \`get\` on the \`X\` for "x" has \`v=1\`` then `And "a" does an \`inc\` on \`X\` of "x"`.

**Where in the skills.** `python/references/testing-features.md`, Errors table (the `Step definition is not found:` row); `reboot/bdd/steps.py` for the hint.
