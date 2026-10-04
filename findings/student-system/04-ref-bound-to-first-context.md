---
id: student-system-04
project: student-system
source: "student-system/reboot-findings.md §4"
reboot_version: 1.5.0
severity: unrated
target: plugin
names:
  - python/references/rpc-refs.md
  - python/references/testing-harness.md
  - python/references/patterns-common-gotchas.md
tags: [negative-space, error-text, testing]
cluster: "4.1"
still_applies: unknown
status: Resolved
resolved_by: "python/references/rpc-refs.md § Never"
---

# A ref() is bound to the first context that uses it; the rule is documented only under "concurrent callers"

**What happened.** `testing-harness.md` mentions `MixedContextsError` in one bullet about "one external context per concurrent caller". It was hit serially, four times, with no concurrency: a test held `program = Program.ref("BS-CS")`, proposed with the registrar's context, then approved with a second registrar's context. The error text is good: "This `WeakReference` for `Program` with ID 'BS-CS' has previously been used by a different `Context`. That is not allowed. Instead create a new `WeakReference` for every `Context`."

**Expected.** Say this where `ref()` is introduced (`rpc-refs.md`), not only in the testing reference, and show the idiom: hold ids, call `Type.ref(id)` inline per call.

**Repro.** Not recorded.

**Where in the skills.** `python/references/rpc-refs.md` (where `ref()` is introduced) and `python/references/testing-harness.md`.

**Checked at 1.6.0.** `python/references/patterns-common-gotchas.md` §20 and `python/references/testing-harness.md` (line ~308) now document `MixedContextsError` and the fresh-ref-per-context idiom. `rpc-refs.md` itself does not mention it, so the placement ask is not met.
