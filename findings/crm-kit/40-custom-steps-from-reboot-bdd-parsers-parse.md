---
id: crm-kit-40
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §6"
reboot_version: 1.6.0
severity: unrated
target: bdd
names:
  - python/references/testing-features.md
tags: [testing, error-text]
cluster: "4.4"
duplicate_of: reboot-crm-46
still_applies: no
status: Resolved
resolved_by: "python/references/testing-features.md § Never"
---

# Take async custom-step decorators from reboot.bdd and always wrap patterns in parsers.parse(...)

**What happened.** An `async def` under `pytest_bdd`'s decorators is never awaited: it "passes", and the next step fails with "Expected a preceding step to have made a call". A plain-string pattern registers nothing and fails much later with `StepDefinitionNotFoundError`.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `python/references/testing-features.md` § Never covers the missing `parsers.parse(...)`, and its examples import `parsers, then, when` from `reboot.bdd`; nothing warns that `pytest_bdd`'s own decorators leave an `async def` un-awaited (grep `pytest_bdd`).
