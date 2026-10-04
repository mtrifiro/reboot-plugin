---
id: reboot-crm-06
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P0.6"
reboot_version: 1.6.0
severity: red
target: bdd
names:
  - feature/SKILL.md
  - python/references/testing-features.md
tags: [testing, negative-space, error-text]
cluster: "4.1"
still_applies: yes
status: Open
resolved_by: ""
---

# A saved value inside quotes is silently the literal text, and the failure surfaces somewhere else

**What happened.** `scope_id=<northwind id>` recalls a saved value; `scope_id="<northwind id>"` passes the fourteen characters `<northwind id>` as the value. Both parse and run, and the second reaches the servicer as an account id nobody created, which aborted with `StateNotConstructed` on a state type two calls away from the wrong step. The convention is consistent (`tail=<alpha tail>` has no quotes; `of "<acme id>"` in the state-id position has them), but the quoted form is the one a reader writes first because every other string value is quoted.

**Expected.** Either a quoted `<name>` matching a saved value is substituted too, or the step fails at parse time ("`<northwind id>` looks like a saved value; write it without quotes to recall it"). Source fix options: (1) parse-time error (recommended), (2) substitute quoted forms, (3) skill shows bare and quoted forms side by side in `feature/SKILL.md` and `testing-features.md`.

**Repro.** Write a step with `scope_id="<saved name>"` instead of `scope_id=<saved name>` where the value was saved earlier in the scenario.

**Where in the skills.** `feature/SKILL.md`, `python/references/testing-features.md`.

**Checked at 1.6.0.** `python/references/testing-features.md` (lines ~110-118) shows both forms in different positions but never states the rule; `feature/SKILL.md` has no such note.
