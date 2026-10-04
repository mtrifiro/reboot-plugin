---
id: reboot-crm-21
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P1.11"
reboot_version: 1.6.0
severity: red
target: bdd
names: []
tags: [testing, error-text]
cluster: "4.4"
still_applies: unknown
status: Open
resolved_by: ""
---

# The "Almost" catch-all step matches ordinary web-app text

**What happened.** `_almost_missing_backticks` matches any step whose text contains ` has ` or ` with ` followed by no backticks. The web step `"alice" checks "Bad state has real consequences" in the web app` was swallowed by it and failed with "Almost: each clause goes in backticks", which points nowhere near the cause. The app renamed the label. The app later added `scripts/lint_features.py`, which flags this shape (per the source's Scripts section).

**Expected.** Anchor the catch-all on the clause grammar, exclude the web-app step shapes (`checks|clicks|fills|selects|sees ... in the web app`), or run the catch-all last, only after every real step pattern has failed. Source recommends running it last, implemented via grammar anchoring.

**Repro.** Write a web-app step whose quoted text contains ` has ` or ` with `.

**Where in the skills.** Not applicable to a skill (reboot.bdd).
