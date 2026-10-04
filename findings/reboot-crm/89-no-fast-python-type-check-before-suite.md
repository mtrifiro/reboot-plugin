---
id: reboot-crm-89
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md A.8"
reboot_version: 1.6.0
severity: yellow
target: primer
names:
  - python/references/lifecycle-project-setup.md
tags: [testing, scaffold, cost]
cluster: "B"
still_applies: unknown
status: Open
resolved_by: ""
---

# No fast Python type check before a three-minute test run

**What happened.** A missing import, a misspelled generated name or a keyword the request lacks each surfaced only after a test module ran, minutes per cycle. The dashboard's pyright ran out of heap on this app (P1.12), probably why nothing replaced it. Status: done 2026-10-04: `pyrightconfig.json` scopes pyright to `backend/src` with the generated code on its path, about seven seconds with an 8 GB Node heap; `scripts/suite.sh` runs it first. First run found eight: one real (`Lead.create` could be given `None` for `imported_by_id`), two tidy-ups, five false positives from annotations read against generated types.

**Expected.** `pyright backend/src` scoped to hand-written code as a step before the suite.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.
