---
id: restaurant-app-3-15
project: restaurant-app-3
source: "restaurant-app-3/FINDINGS.md § Things that worked, item 3"
reboot_version: 1.6.0
severity: green
target: positive
names:
  - python/references/errors.md
  - python/references/testing-features.md
tags: [pattern, error-text]
cluster: ""
still_applies: unknown
status: Open
resolved_by: ""
---
# Errors tables in the references diagnosed every error without opening generated code

**What happened.** Every Reboot error the build hit (generated request names, `Literal` validation, context types) was diagnosable from the reference that owns it, without opening generated code.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** `python/references/errors.md`; the Errors table in each reference.
