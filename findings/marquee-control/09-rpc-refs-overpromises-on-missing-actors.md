---
id: marquee-control-09
project: marquee-control
source: "v 1.4.1 Reboot/Archive/marquee-control/docs/reboot-learnings.md §2026-08-17 build session, bullet 9"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/rpc-refs.md
tags: [negative-space, error-text]
cluster: ""
duplicate_of: cineloop-33
still_applies: no
status: Resolved
resolved_by: "python/references/rpc-refs.md § Never"
---

# rpc-refs.md overpromises on missing actors: a no-factory singleton never written aborts too

**What happened.** `rpc-refs.md` says 'a reader call on a non-existent actor returns the zero-valued state'. That is not what happens for a no-factory singleton that was never written: the reader aborts `StateNotConstructed`, wrapped as the calling transaction's `<Method>Aborted('Unknown')`, so the real cause hides one level down. Same behavior port-meridian hit reactively. Guard with `except <Type>.GetAborted` plus `isinstance(aborted.error, errors_pb2.StateNotConstructed)`.

**Expected.** Not recorded.

**Repro.** Read a factory-less singleton that nothing has written yet, from inside a transaction.

**Where in the skills.** `python/references/rpc-refs.md`. Same gap as cineloop-33; this sighting shows it is not limited to factory types.

**Checked at 1.6.0.** `rpc-refs.md` § "Does this actor exist?" now says the reader aborts for every type, with or without a factory, and gives the `isinstance(aborted.error, StateNotConstructed)` probe; § Never forbids assuming zero state. The `Unknown` wrapping when the abort crosses an undeclaring transaction is covered generally by the `propagating as 'Unknown'` row in `errors.md`.
