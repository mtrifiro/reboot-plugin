---
id: plugin-browser-10
project: plugin-browser
source: "plugin-browser/FINDINGS.md § reboot.bdd, item 1"
reboot_version: 1.6.0
severity: yellow
target: bdd
names:
  - python/references/testing-features.md
  - python/references/api-pydantic.md
  - python/references/errors.md
tags: [testing, error-text, negative-space]
cluster: ""
still_applies: yes
status: Open
resolved_by: ""
---
# A response field named `where` can't be asserted in a built-in step

**What happened.** ``has `versions[0].where="1.6.0"` `` failed with `ValueError: Invalid property \`versions[0].where\`: Parse error at 1:12 near token where (WHERE)`. The step's property path goes through jsonpath_ng, where `where` is a keyword. Renaming the field to `checkout` passed. (2026-10-11, the Next page.)

**Expected.** Any valid pydantic field name works in a clause, or the skills list the names that don't.

**Repro.** A response model with a field `where`, asserted as `` `where="x"` `` in a ``Then as "alice", `m` on the `T` for "id" has …`` step.

**Where in the skills.** `python/references/testing-features.md` (the clause syntax) and `api-pydantic.md` (field names to avoid); `errors.md` has no row for `JsonPathParserError`. Checked at import: no skill mentions jsonpath or `where`.
