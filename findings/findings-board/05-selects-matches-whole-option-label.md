---
id: findings-board-05
project: findings-board
source: "findings-board/FINDINGS.md § reboot.bdd, item 4"
reboot_version: 1.6.0
severity: yellow
target: bdd
names:
  - python/references/testing-web-app.md
tags: [testing, frontend]
cluster: ""
still_applies: yes
status: Open
resolved_by: ""
---
# The `selects` web step matches an option's whole label, so options showing counts can't be picked by value

**What happened.** `"alice" selects "Reboot" in "Fix owner" in the web app` timed out against a chip whose options read `Reboot (1)`: the step calls `select_option(label=...)`, an exact match on the option's text, while the reference (`testing-web-app.md`, "Picks an option in the select with that label") reads as if the value would do. Playwright matches a bare string against value or label; the step's `label=` does not. Workaround: render the option text as the plain value (counts elsewhere), or write the full option text in the step.

**Expected.** The step to pick by value or label, as Playwright's bare string does, or the reference to say the option's whole text is matched.

**Repro.** A select whose option text differs from its value (`<option value="Reboot">Reboot (1)</option>`); `selects "Reboot" in "<label>"`.

**Where in the skills.** `python/references/testing-web-app.md`, the steps table ("Picks an option in the select with that label") and "Accessible markup the steps need" ("its options' text"), which don't say the match is exact on the whole text.
