---
id: reboot-crm-71
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P4.2"
reboot_version: 1.6.0
severity: green
target: framework
names:
  - python/references/stdlib-ordered-map.md
tags: [negative-space, error-text]
cluster: "4.1"
still_applies: unknown
status: Resolved
resolved_by: "python/references/stdlib-ordered-map.md § Limits"
---

# There is no way to ask whether an OrderedMap exists; a reader over a maybe-empty one catches the abort

**What happened.** `stdlib-ordered-map.md` says a map is constructed by its first insert and reading it before then aborts. A reader that looks up an address in a map that may never have had an insert has no `exists` to ask and no `found=False` to receive: it gets `OrderedMap.SearchAborted` and must catch it and decide it means nothing there.

**Expected.** Fix proposed: have `search` answer `found=False` on an unconstructed map, or add an `exists` reader. Recommendation: `found=False`, which removes the try/except from every first read without new API surface.

**Repro.** Not recorded.

**Where in the skills.** `python/references/stdlib-ordered-map.md`.

**Checked at 1.6.0.** `python/references/stdlib-ordered-map.md` documents the abort (lines ~17, 108) and recommends `create` up front; no `exists` reader (framework behaviour).
