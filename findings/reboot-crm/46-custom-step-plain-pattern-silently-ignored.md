---
id: reboot-crm-46
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P3.10"
reboot_version: 1.6.0
severity: yellow
target: bdd
names:
  - python/references/testing-features.md
tags: [testing, error-text]
cluster: "4.4"
still_applies: unknown
status: Open
resolved_by: ""
---

# A custom step declared with a plain f-string pattern is silently ignored

**What happened.** `@then('the research prompt mentioned "{text}"')` without `parsers.parse(...)` registers nothing and surfaces later as `StepDefinitionNotFoundError`. `testing-features.md` does show `parsers.parse`, so this is not a documentation gap but a silent no-op.

**Expected.** Fix proposed: warn at decoration time ("pattern contains `{...}` but is not a parser; wrap it in `parsers.parse(...)`"). Recommendation: do it; the check is local and certain.

**Repro.** Decorate a step with a plain string containing `{...}` and run a scenario that uses it.

**Where in the skills.** `python/references/testing-features.md` (custom steps, `parsers.parse` example ~line 328).

**Checked at 1.6.0.** `testing-features.md` shows `parsers.parse` (line ~328); no error-index row for `StepDefinitionNotFoundError` from this cause was checked.
