---
id: student-system-02
project: student-system
source: "student-system/reboot-findings.md §2"
reboot_version: 1.5.0
severity: unrated
target: plugin
names:
  - python/references/stdlib-ordered-map.md
  - python/references/testing-harness.md
  - python/references/lifecycle-initialize-hook.md
tags: [negative-space, error-text, testing]
cluster: "4.1"
still_applies: unknown
status: Resolved
resolved_by: "python/references/testing-harness.md § Limits"
---

# Reading an OrderedMap before its first insert aborts with StateNotConstructed, and the failed run hung the test suite

**What happened.** The reference said construction is implicit on insert but not what `range` or `search` does before that. It aborts: `OrderedMap.SearchAborted: aborted with 'StateNotConstructed'`. The catalog page and the student list both read the index before anything had been added. The first attempted fix (make `Institution.create` a transaction that constructs the maps) did not fail the suite but hung it: `pytest` sat with no output until killed and the interim log was read. Reboot Air finding 3 (reboot-air-03) is the same shape: a raise inside the `initialize` path keeps `Reboot().up()` retrying with backoff instead of surfacing an error. The app's fix: `InstitutionServicer._page` catches `OrderedMap.RangeAborted` and returns an empty page.

**Expected.** The reference should say "reads on an unconstructed map abort; catch `RangeAborted` or insert first", and the test harness should turn an `initialize` failure into a test failure.

**Repro.** Not recorded.

**Where in the skills.** `python/references/stdlib-ordered-map.md`; `python/references/testing-harness.md` (hang on failing `initialize`).

**Checked at 1.6.0.** `python/references/stdlib-ordered-map.md` (lines ~17, 108) now says reads on an unconstructed map abort with `StateNotConstructed` and to `create` up front, so the first half is covered. No text in `testing-harness.md` or `lifecycle-initialize-hook.md` mentions a hanging `up()` when `initialize` fails; the harness behaviour itself is framework-side.
