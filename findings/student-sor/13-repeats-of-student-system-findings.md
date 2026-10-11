---
id: student-sor-13
project: student-sor
source: "student-sor/reboot-findings.md §8"
reboot_version: 1.5.0
severity: unrated
target: plugin
names:
  - python/references/rpc-refs.md
  - python/references/stdlib-ordered-map.md
  - python/references/patterns-common-gotchas.md
  - run/SKILL.md
tags: [contradiction, negative-space, operations]
cluster: "4.1"
still_applies: yes
status: Resolved
resolved_by: "python/references/rpc-refs.md § Do this; python/references/stdlib-ordered-map.md § Errors you will see"
---

# Repeats of student-system findings, hit again

**What happened.** Four repeats: (1) Readers on a factory-constructed actor that does not exist abort with `StateNotConstructed` instead of returning zero state (`rpc-refs.md` still says otherwise); probes in `servicers/common.py` catch `<Type>.GetAborted` (student-system-03). (2) `OrderedMap.range` on a map with no inserts aborts; `range_page` catches `RangeAborted` (student-system-02). (3) `MixedContextsError` when one `ref()` is used from two contexts; the author still wrote a test that did it, holding `Student.ref(sid)` and calling it as registrar, then as student. The error message is excellent; the rule should be next to `ref()` in `rpc-refs.md` (student-system-04). (4) Envoy from a killed `rbt dev run` keeps the port; `lsof -t -iTCP:9993 -sTCP:LISTEN | xargs kill` before restarting (student-system-11).

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** `rpc-refs.md`, `run/SKILL.md`.

**Checked at 1.6.0.** `python/references/rpc-refs.md` line ~105 still says reader returns zero-valued state; `run/SKILL.md` has no stop/restart guidance. The `MixedContextsError` rule now exists in `patterns-common-gotchas.md` §20 but not in `rpc-refs.md`.

**Resolution (2026-10-10).** `rpc-refs.md` § Do this ("Does this actor exist?") says a reader on a never-constructed actor aborts `StateNotConstructed` for every type, with or without a factory, and shows the `isinstance(aborted.error, StateNotConstructed)` probe; § Never forbids assuming zero state; the Errors table carries the per-probe WARNING. `stdlib-ordered-map.md` has the `SearchAborted`/`RangeAborted` row and `rpc-constructor-calls.md` the `.idempotently()` constructor row.
