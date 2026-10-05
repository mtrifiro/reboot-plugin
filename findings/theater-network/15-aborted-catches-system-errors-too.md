---
id: theater-network-15
project: theater-network
source: "theater-network/docs/reboot-findings.md §15"
reboot_version: 1.4.0
severity: unrated
target: plugin
names:
  - python/references/api-errors.md
  - python/references/patterns-error-handling.md
  - python/references/rpc-constructor-calls.md
tags: [negative-space, error-text]
cluster: "4.1"
still_applies: unknown
status: Resolved
resolved_by: "python/references/patterns-error-handling.md § Never; python/references/rpc-constructor-calls.md § Never"
---

# Generated <Method>Aborted catches SYSTEM errors too

**What happened.** `except Seat.PlaceAborted:` does not mean 'the typed error I declared': a ping timeout under load arrives as `PlaceAborted` too. A broad `except ...: pass` around a constructor call silently swallowed timed-out placements and the room claimed complete with seats missing; only the audit's expensive recompute caught it. The same bug pattern hid in every `except <X>Aborted: pass` written for 'already exists' tolerance (`add_theater`, `add_showing`); all now re-raise anything that is not `StateAlreadyConstructed`.

**Expected.** Always inspect `aborted.error` (source shows `if not isinstance(aborted.error, errors_pb2.StateAlreadyConstructed): raise`; proto-era name).

**Repro.** Under load, a constructor call times out and is swallowed by a broad `except <X>Aborted: pass`.

**Where in the skills.** `api-errors.md`, `patterns-error-handling.md` (Never line).

**Checked at 1.6.0.** `api-errors.md:93` and `patterns-error-handling.md:65` show `isinstance(e.error, OverdraftError)` for declared errors, but I did not find text saying system errors (timeouts) also arrive as `<Method>Aborted`. Not conclusive either way.
