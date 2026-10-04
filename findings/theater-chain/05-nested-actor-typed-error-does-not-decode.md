---
id: theater-chain-05
project: theater-chain
source: "theater-chain/reboot-findings.md §5"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/api-errors.md
  - python/references/patterns-error-handling.md
tags: [negative-space, error-text]
cluster: "4.1"
still_applies: yes
status: Open
resolved_by: ""
---

# Nested actor typed error does not decode at the outer caller

**What happened.** `User.add_seats` (a `Transaction`) calls `Showing.hold_seats` (a `Writer`), and both declare `SeatUnavailableError`. When the inner one aborts the caller does get a `User.AddSeatsAborted`, but `.error` comes back empty. Log: `WARNING Propagating unhandled but declared error (in 'theater.v1.User.AddSeats') aborted with 'ShowingHoldSeatsErrors { seat_unavailable_error { seat_id: "G5" status: "held" } }'`. `assert isinstance(error, SeatUnavailableError)` fails against the empty payload; the inner error is still wrapped in the inner method's error union, which the outer union has no case for. Without a fix the browser gets a generic failure rather than "seat G5 was just taken". Workaround: catch and re-raise at every boundary where the payload must survive: `try: await showing.hold_seats(context, ...) except Showing.HoldSeatsAborted as aborted: if isinstance(aborted.error, SeatUnavailableError): raise User.AddSeatsAborted(SeatUnavailableError(seat_id=aborted.error.seat_id, status=aborted.error.status)) from None; raise`.

**Expected.** Add a "Typed Errors Don't Cross Actor Boundaries Intact" section with the re-raise recipe to `api-errors.md`, which documents raising and catching but not propagation.

**Repro.** Not recorded.

**Where in the skills.** `python/references/api-errors.md`.

**Checked at 1.6.0.** Still absent. Grep of `python/references/api-errors.md` and `python/references/patterns-error-handling.md` for propagate / boundary / empty / re-raise found no cross-actor propagation guidance (only a generic let-errors-propagate note at `patterns-error-handling.md:80`).
