---
id: reboot-air-150-02
project: reboot-air-150
source: "reboot-air/reboot-findings.md §2"
reboot_version: 1.5.0
severity: unrated
target: plugin
names:
  - python/references/rpc-refs.md
tags: [contradiction, error-text, negative-space]
cluster: "4.1"
duplicate_of: cineloop-33
still_applies: yes
status: Resolved
resolved_by: "python/references/rpc-refs.md § Do this"
---

# A reader on a not-yet-constructed actor aborts; the reference says it returns zero state

**What happened.** For a `Type` with an explicit `factory=True` constructor, `await Airline.ref(id).cities(context)` on a never-created actor raises `Airline.CitiesAborted: aborted with 'StateNotConstructed'`; the same holds for `Flight.get` on an unknown flight id. Two patterns built on the documented behaviour broke: an "is the catalog seeded yet?" probe in `initialize`, and an "unknown flight id" check in a transaction. The abort is undeclared, so from a transaction it would also poison the caller's context with an "uncertain mutation". Workaround: catch `<Type>.<Reader>Aborted` and treat it as "does not exist".

**Expected.** The reference should say the zero-state behaviour only applies to types without a factory (if that is the rule), and name `StateNotConstructed` as what a factory-typed reader raises.

**Repro.** Not recorded.

**Where in the skills.** `python/references/rpc-refs.md`, "Refs Don't Materialize Actors": "A reader call on a non-existent actor returns the zero-valued state."

**Checked at 1.6.0.** `python/references/rpc-refs.md` line ~105 still says a reader on a non-existent actor returns the zero-valued state.

**Resolution (2026-10-10).** `rpc-refs.md` § Do this ("Does this actor exist?") says a reader on a never-constructed actor aborts `StateNotConstructed` for every type, with or without a factory, and shows the `isinstance(aborted.error, StateNotConstructed)` probe; § Never forbids assuming zero state; the Errors table carries the per-probe WARNING. `stdlib-ordered-map.md` has the `SearchAborted`/`RangeAborted` row and `rpc-constructor-calls.md` the `.idempotently()` constructor row.
