---
id: findings-board-02
project: findings-board
source: "findings-board/FINDINGS.md § reboot.bdd, item 2"
reboot_version: 1.6.0
severity: yellow
target: bdd
names:
  - python/references/testing-web-app.md
tags: [testing, error-text]
cluster: ""
duplicate_of: reboot-crm-21
still_applies: yes
status: Resolved
resolved_by: "python/references/testing-web-app.md § Never"
---
# A web-step text containing " with " fails "Almost: each clause goes in backticks"

**What happened.** `"alice" eventually sees "What happened with P1.2." in the web app` is swallowed by the catch-all. `testing-web-app.md` § Never does name ` has ` and ` with `, but the error points at backticks, not the word. Workaround: reword the text.

**Expected.** The error names the word, not backticks.

**Repro.** A web-app step whose quoted text contains ` with `.

**Where in the skills.** `python/references/testing-web-app.md` § Never (documented).
