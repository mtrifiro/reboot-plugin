---
id: plugin-browser-11
project: plugin-browser
source: "plugin-browser/FINDINGS.md § Plugin skills, item 7"
reboot_version: 1.6.0
severity: yellow
target: bdd
names:
  - python/references/testing-web-app.md
tags: [testing, error-text]
cluster: ""
duplicate_of: reboot-crm-21
still_applies: no
status: Resolved
resolved_by: "python/references/testing-web-app.md § Never"
---
# A web app step whose quoted name contains " has " is refused as a state check

**What happened.** `When "alice" clicks the "A widget's size has no documented range" link in the web app` failed with ``ValueError: Almost: each clause goes in backticks, e.g. `amount=50` ``. reboot.bdd's "almost" step `.+ (?:with|has) <unbackticked clauses>$` matches any step containing ` has ` or ` with `, quoted text included, before the built-in click step can. Renaming the link's text was the only way round it. (2026-10-12, the reboot-findings entries list.)

**Expected.** Quoted names in web app steps to be taken as names, whatever words they hold.

**Repro.** Any `clicks the "... has ..." link in the web app` or `sees "... with ..." in the web app` step.

**Where in the skills.** `python/references/testing-web-app.md` says nothing about it, per the source. Checked at import: § Never names quoted web text containing ` has ` or ` with `, and § Errors you will see has the `Almost` row; the same project's plugin-browser-01 hit it with a `sees` step. The guard itself is reboot-crm-21.
