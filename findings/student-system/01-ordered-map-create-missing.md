---
id: student-system-01
project: student-system
source: "student-system/reboot-findings.md §1"
reboot_version: 1.5.0
severity: unrated
target: plugin
names:
  - python/references/stdlib-ordered-map.md
tags: [version-drift, error-text]
cluster: "A"
still_applies: no
status: Obsolete
resolved_by: ""
---

# stdlib-ordered-map shows OrderedMap.create(...); the class has no such method

**What happened.** The reference ("Construct Explicitly or Implicitly") showed `await OrderedMap.create(context, self.state.account_ids_map_id)`. `mypy` reported `"type[OrderedMap]" has no attribute "create"` and no constructor classmethod was found in `ordered_map_rbt.py`. Only the implicit form (first `insert` constructs the map) existed. The app worked around it: `Institution.create` only allocates the two map ids and the indexes come into being on the first `add_course` / `add_student`.

**Expected.** The reference should drop the explicit form or say which version has it.

**Repro.** Not recorded.

**Where in the skills.** `python/references/stdlib-ordered-map.md`, "Construct Explicitly or Implicitly".

**Checked at 1.6.0.** `python/references/stdlib-ordered-map.md` (lines ~44, 94) now documents `create` as a transaction called on a ref: `OrderedMap.ref(id).create(context)`, not a classmethod. The reported form is gone.
