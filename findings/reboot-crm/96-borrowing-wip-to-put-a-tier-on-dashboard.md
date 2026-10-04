---
id: reboot-crm-96
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md What worked: borrowing `@wip` to put a tier on the dashboard"
reboot_version: 1.6.0
severity: green
target: positive
names:
  - python/references/testing-features.md
tags: [pattern, testing]
cluster: "E"
still_applies: unknown
status: Open
resolved_by: ""
---

# What worked: borrowing @wip to put a tier on the dashboard

**What happened.** The dashboard only highlights `@wip` (see reboot-crm-79). To review the critical tier there, `@wip` was put beside `@critical` on all 47 scenarios in one scripted pass, and the dashboard's work-in-progress filter became exactly that tier; `-m wip` selected the same 47, so dashboard and command line agreed. A second pass took `@wip` off after the review. It works because a Gherkin tag is only a label: the harness runs a `@wip` scenario like any other. Cautions: take it off when the review is done or `@wip` stops meaning "not yet agreed"; check first that nothing else is `@wip` (`-m "wip and not critical"` should collect nothing). Area: Dashboard / reboot.bdd.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.
