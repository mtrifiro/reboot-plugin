---
id: cineloop-33
project: cineloop
source: "cineloop/reboot-findings.md §23 (Part 4)"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/rpc-refs.md
  - python/references/stdlib-ordered-map.md
  - python/references/state-collections.md
tags: [contradiction, error-text, negative-space]
cluster: "4.1"
still_applies: yes
status: Resolved
resolved_by: "python/references/rpc-refs.md § Do this; python/references/stdlib-ordered-map.md § Errors you will see"
---

# A reader on an unconstructed actor aborts if the type has a factory (rpc-refs.md is wrong)

**What happened.** `rpc-refs.md` says 'A reader call on a non-existent actor returns the zero-valued state.' That is only true for a `Type` with no explicit constructor. `Theater` declares `create=Writer(..., factory=True)`, and reading one that was never created raises `Theater.GetAborted` with `StateNotConstructed`. Adding a `Theater.get` lookup inside checkout (to denormalise the city onto the receipt) broke three previously passing tests because the test harness seeded a showing without its theater. The right fix was not seeding theaters but noticing the city is decorative and a purchase must not fail because a decorative lookup did (`try: ... except Theater.GetAborted: theater_city = ""`). Lesson: when adding a cross-actor read to an existing flow, decide what happens if it fails before deciding what it returns.

**Expected.** Replace the sentence in `rpc-refs.md`: with no `factory=True` method the read returns zero-valued state; with one, the read aborts with `StateNotConstructed` because the constructor is the only path into existence. Wrap cross-actor reads of constructor-bearing types in a `try` unless the caller can guarantee existence.

**Repro.** Read an actor of a factory type that was never constructed (e.g. a test harness that skips seeding it).

**Where in the skills.** `python/references/rpc-refs.md` 'Refs Don't Materialize Actors'. Contradicts `stdlib-ordered-map.md` (lines ~108) and `state-collections.md` (~203), which say reads abort with `StateNotConstructed`.

**Checked at 1.6.0.** `python/references/rpc-refs.md` lines 100-110 still read 'A reader call on a non-existent actor returns the zero-valued state' with no factory caveat.

**Resolution (2026-10-10).** `rpc-refs.md` § Do this ("Does this actor exist?") says a reader on a never-constructed actor aborts `StateNotConstructed` for every type, with or without a factory, and shows the `isinstance(aborted.error, StateNotConstructed)` probe; § Never forbids assuming zero state; the Errors table carries the per-probe WARNING. `stdlib-ordered-map.md` has the `SearchAborted`/`RangeAborted` row and `rpc-constructor-calls.md` the `.idempotently()` constructor row.
