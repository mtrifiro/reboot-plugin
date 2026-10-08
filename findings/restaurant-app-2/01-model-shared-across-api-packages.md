---
id: restaurant-app-2-01
project: restaurant-app-2
source: "restaurant-app-2/FINDINGS.md § Framework, item 1"
reboot_version: 1.6.0
severity: yellow
target: framework
names:
  - python/references/api-pydantic.md
tags: [error-text]
cluster: ""
still_applies: yes
status: Open
resolved_by: ""
---
# A Model shared across API packages forces per-package copies

**What happened.** Splitting one API into five packages (`house`, `bookings`, `floor`, `checks`, `kitchen`), every package needed its own `Rejected` error model and `floor` needed its own copy of the checks' `VisitSummary` (`SeatedParty`). Not reproduced; the author followed the documented limit to avoid it. Per `api-pydantic.md` § Limits, `rbt generate` exits 0 but the generated `_rbt.py` refers to the other package's Model without importing it, then fails at import with `NameError`. That reads as a codegen bug (a missing import), not a design limit. The copies are also distinct types: a nested call's `Rejected` must be caught and re-raised as the caller's own `Rejected`.

**Expected.** One shared error model (and response models) importable by every package.

**Repro.** Define `class Rejected(Model)` in `api/a/v1/a.py`, use it in `errors=[Rejected]` on a method in `api/b/v1/b.py`, run `rbt generate`, then import `b.v1.b_rbt`.

**Where in the skills.** `python/references/api-pydantic.md` § Limits (documented, with workaround).
