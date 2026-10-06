---
id: crm-kit-09
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §2"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/api-pydantic.md
tags: [negative-space, error-text, pattern]
cluster: "4.1"
duplicate_of: reboot-crm-26
still_applies: no
status: Resolved
resolved_by: "python/references/api-pydantic.md § Limits"
---

# Split the API into domain packages from day one and never name one package's Model inside another

**What happened.** `rbt generate` exits 0, but the generated Python names a foreign model without importing it (`NameError: name 'common' is not defined`). A package with models but no `Type` generates nothing. Splitting later renames every type (the state-ref prefix hashes the full name), which costs an expunge. The shape that works: bases in `api/shared.py` (no `API(...)` block), an empty subclass per package (`class HistoryEntry(HistoryEntryBase): """This package's own copy."""`), and constants in `api/vocabulary.py`. Only a model that nests no other model can be a base; a model that holds rows is declared per package; a value crossing packages is converted by value, and mypy misses those crossings, so the suite finds them. Don't name a package after a `backend/src/` module: `api/assistant/` shadowed `backend/src/assistant.py`.

**Expected.** Domain packages `api/<pkg>/v1/<pkg>.py` from day one; shared bases subclassed per package.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `python/references/api-pydantic.md` § Limits (lines ~140-148) documents the missing import, the no-`Type` package generating nothing, and the shared-base workaround. The rename-on-split cost and the `backend/src/` shadowing were not found (grep `shadow`).
