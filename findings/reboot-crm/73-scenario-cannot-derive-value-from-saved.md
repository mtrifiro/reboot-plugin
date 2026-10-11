---
id: reboot-crm-73
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P4.4"
reboot_version: 1.6.0
severity: green
target: plugin
names:
  - python/references/testing-features.md
tags: [testing, index-gap]
cluster: "4.1"
still_applies: unknown
status: Resolved
resolved_by: "python/references/testing-features.md § Limits"
---

# A scenario cannot derive a value from a saved one

**What happened.** A record's address is its name plus a tail, and a scenario resolving by the tail alone needs the tail of a saved id. Built-in steps can save a response property and substitute it back but cannot take a substring or compute from it, so the feature carries two custom steps (`the tail of "<id>" is saved as`, `the id "<id>" reads as "..." and a tail`) for what is one line of Python. Not wrong; custom steps are the documented answer.

**Expected.** Fix proposed: document custom steps as the answer for deriving one value from another (one worked example), or add a small expression language over saved values. Recommendation: the documentation, not the language.

**Repro.** Not recorded.

**Where in the skills.** `python/references/testing-features.md` custom-steps section.

**Checked at 1.6.0.** Custom steps exist in `testing-features.md` (tags list includes `custom-steps`); no worked example of deriving a value from a saved one was found.
