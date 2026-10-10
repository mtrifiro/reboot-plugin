---
id: plugin-browser-01
project: plugin-browser
source: "plugin-browser/FINDINGS.md § reboot.bdd, item 1"
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
# A " has " inside a step's quoted text trips "Almost: each clause goes in backticks"

**What happened.** `Then "alice" eventually sees "A widget has a name and a size" in the web app within 30 seconds` failed with `ValueError: Almost: each clause goes in backticks`. The step has no clauses; the guard (`_almost_missing_backticks` in `reboot/bdd/steps.py`) matches the word "has" inside the quoted text. Workaround: assert `"a name and a size"`.

**Expected.** The guard ignores quoted text, or the error names the word. `testing-features.md` § Errors and `errors.md` give this error one cause, a clause without backticks; `testing-web-app.md` § Never does name ` has ` and ` with `, but the error row doesn't point there.

**Repro.** A built-in web step whose quoted text contains " has " or " with ".

**Where in the skills.** `python/references/testing-web-app.md` § Never (documented); the error rows in `testing-features.md` and `errors.md` name only the backtick cause.
