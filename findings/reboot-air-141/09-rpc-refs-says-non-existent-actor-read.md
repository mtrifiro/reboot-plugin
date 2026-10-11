---
id: reboot-air-141-09
project: reboot-air-141
source: "reboot-air/REBOOT_FINDINGS.md §9"
reboot_version: 1.4.1
severity: red
target: plugin
names:
  - python/references/rpc-refs.md
  - python/references/stdlib-ordered-map.md
tags: [contradiction, error-text, negative-space]
cluster: "4.1"
duplicate_of: cineloop-33
still_applies: yes
status: Resolved
resolved_by: "python/references/rpc-refs.md § Do this"
---

# rpc-refs says non-existent actor read returns zero state; it aborts

**What happened.** `rpc-refs.md`, "Refs Don't Materialize Actors", states: "A reader call on a non-existent actor returns the zero-valued state." It actually aborts: `airline.v1.fleet_rbt.Airport.DetailsAborted: aborted with 'StateNotConstructed'`. The author designed a validation path on the documented behaviour (`Plane.rebase` reads the `Airport` actor and treats an empty `iata` as "not on our network"). It type-checked and read correctly and failed only in the one negative-path test, a full 10-minute suite run in. An app without that test ships the bug. `errors_pb2` comes from `rbt.v1alpha1`, which no reference mentions; the author found it by grepping `site-packages`. The sentence may have been copied into other references.

**Expected.** Correct the sentence to say the call aborts with `StateNotConstructed`; show the idiom `try: await Airport.ref(iata).details(context) except Airport.DetailsAborted as aborted: if not isinstance(aborted.error, errors_pb2.StateNotConstructed): raise` for "does this actor exist?"; export or document `StateNotConstructed` somewhere reachable.

**Repro.** Call a reader on an actor that was never constructed, e.g. `Airport.ref(iata).details(context)` for an unknown `iata`.

**Where in the skills.** `python/references/rpc-refs.md`, "Refs Don't Materialize Actors".

**Checked at 1.6.0.** Still present. `python/references/rpc-refs.md:104-106` still says a reader on a non-existent actor "returns the zero-valued state". It now contradicts `python/references/stdlib-ordered-map.md:17,108` and `python/references/state-collections.md:203`, which say reads abort with `StateNotConstructed`.

**Resolution (2026-10-10).** `rpc-refs.md` § Do this ("Does this actor exist?") says a reader on a never-constructed actor aborts `StateNotConstructed` for every type, with or without a factory, and shows the `isinstance(aborted.error, StateNotConstructed)` probe; § Never forbids assuming zero state; the Errors table carries the per-probe WARNING. `stdlib-ordered-map.md` has the `SearchAborted`/`RangeAborted` row and `rpc-constructor-calls.md` the `.idempotently()` constructor row.
