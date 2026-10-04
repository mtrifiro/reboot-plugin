---
id: student-sor-12
project: student-sor
source: "student-sor/reboot-findings.md §7"
reboot_version: 1.5.0
severity: green
target: positive
names:
  - python/references/servicer-transaction.md
  - python/references/patterns-common-gotchas.md
  - python/references/auth-allow-if.md
  - python/references/stdlib-ordered-map.md
tags: [pattern, index-gap]
cluster: "E"
still_applies: unknown
status: Open
resolved_by: ""
---

# Things that worked and are worth documenting because the author could not find them

**What happened.** Four behaviours worked but no reference documents them. (1) A Transaction may call another Transaction (the seeder's `Student.import_history` calls `Term.add_to_roster` and `Institution.index_record`, both transactions); `servicer-transaction.md` only shows writers and readers being called. (2) A Writer can call Readers on other actors (used for existence probes and reading the caller's `User` profile from inside a mutation); `patterns-common-gotchas.md` says so in one clause and deserves an example. (3) `context.app_internal` is true inside every nested call, including a `User.set_claims` invoked by the framework, so `allow_if(any=[is_app_internal, predicate])` is the right shape for types other actors call into. (4) The bulk `OrderedMap.insert(entries={key: Item(bytes=...)})` form works from inside a transaction and is the only way to keep a roster insert per term rather than per attempt.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** The four references named above.

**Checked at 1.6.0.** Bulk `entries` is in the `stdlib-ordered-map.md` method table (line ~45). Nested transactions and `app_internal` in nested calls were not found documented.
