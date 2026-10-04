---
id: reboot-air-141-15
project: reboot-air-141
source: "reboot-air/REBOOT_FINDINGS.md §15"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/stdlib-ordered-map.md
tags: [negative-space, error-text]
cluster: "4.1"
still_applies: no
status: Resolved
resolved_by: "python/references/stdlib-ordered-map.md § Construct Explicitly or Implicitly"
---

# Ranging an OrderedMap before first insert aborts

**What happened.** `stdlib-ordered-map.md` said "Or skip `create` and let the first `insert` construct the map implicitly" but did not say that a `range` / `search` before any insert aborts with `StateNotConstructed` rather than returning an empty page. A customer who has signed in but never booked has a valid index ID and no map behind it, so their "My trips" page throws. This is finding §9's rule hit through the stdlib's lazy-construction recommendation. Cost: one test failure 19 minutes into a suite run, on the only test that read an index nobody had written to.

**Expected.** State plainly that a read before the first `insert` raises `StateNotConstructed` and to construct explicitly with `create` if reading before writing; better, make the empty read return an empty page.

**Repro.** Not recorded.

**Where in the skills.** `python/references/stdlib-ordered-map.md`.

**Checked at 1.6.0.** Fixed in the docs. `python/references/stdlib-ordered-map.md:17` and the "Construct Explicitly or Implicitly" section (line 108) now state that reading before construction aborts with `StateNotConstructed` and advise `create` up front; `state-collections.md:203` cross-references it. The framework behaviour itself is unchanged.
