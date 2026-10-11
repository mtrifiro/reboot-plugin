---
id: restaurant-app-3-01
project: restaurant-app-3
source: "restaurant-app-3/FINDINGS.md § Framework, item 1"
reboot_version: 1.6.0
severity: yellow
target: framework
names:
  - python/references/api-pydantic.md
tags: [pattern]
cluster: ""
duplicate_of: reboot-crm-26
still_applies: yes
status: Resolved
resolved_by: "python/references/api-pydantic.md § Limits"
---
# A Model shared across API packages still has to be copied into each one; avoided here only by keeping one package

**What happened.** This build kept its whole API in one package, which is the only reason it never had to copy its `Rejected` error or base models. restaurant-app-2, built from the same brief, split its API and copied `Rejected` into five packages; reboot-crm keeps base classes in `api/shared.py` (its P1.16). Each new app that splits its API pays this again.

**Expected.** Generated code that imports a model from the package that defines it, so packages can share a `Model`. The repeat raises the codegen fix's priority.

**Repro.** Not recorded here (avoided by one package); see restaurant-app-2's `FINDINGS.md` § Framework, item 1 (restaurant-app-2-01).

**Where in the skills.** `python/references/api-pydantic.md`.
