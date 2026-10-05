---
title: Error Handling Patterns
impact: MEDIUM
impactDescription: Inconsistent error handling makes failures opaque to callers
tags: patterns, errors, MethodAborted, catch, propagate, SystemAborted, timeout
summary: "`<Method>Aborted` also carries timeouts and system errors: always inspect `.error` and re-raise what isn't yours; carrying a typed error across actors; no catch-to-log."
step: any
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: ""
---

# Error Handling Patterns

## When you are here

You are calling a method that can abort, from a servicer, a workflow
or a test, and deciding what to catch, what to let through, and how a
typed error from a nested call reaches your own caller. Declaring an
error and raising it is in [`api-errors.md`](api-errors.md).

## Do this

Catch the method's `<Method>Aborted`, branch on the type of `.error`,
and re-raise everything you did not expect:

```python
from bank.v1.account import OverdraftError
from bank.v1.account_rbt import Account

try:
    await Account.ref(account_id).withdraw(context, amount=100)
except Account.WithdrawAborted as aborted:
    if not isinstance(aborted.error, OverdraftError):
        raise
    # aborted.error.amount says how far over the balance this was.
    ...
```

`.error` is typed as the union of the method's declared error `Model`s
**plus** every gRPC error (`DeadlineExceeded`, `Unavailable`,
`Unknown`, …) and every Reboot error (`StateNotConstructed`,
`StateAlreadyConstructed`, …) (1.6.0 source,
`reboot/aio/aborted.py`). The `isinstance` check is what makes the
handler mean "the error I declared".

Typed errors are the contract with the UI: `SeatUnavailableError(seat_ids=[...])`
lets the interface say "F-11 and F-12 were just taken" and repaint
those seats, where a generic exception collapses every case into
"something went wrong" (observed at 1.4.1).

### Carrying a typed error across an actor boundary

If `User.add_seats` calls `Showing.hold_seats` and both declare the
**same** `SeatUnavailableError` class, an uncaught inner abort is
re-raised as `User.AddSeatsAborted` with the payload intact, logging
`Propagating unhandled but declared error` (1.6.0 template). If the
outer method does not declare that exact class, the caller gets
`Unknown`. At 1.4.1 the payload arrived empty; where you must be sure
(or the classes differ), catch and re-raise explicitly:

```python
try:
    await showing.hold_seats(context, seat_ids=request.seat_ids)
except Showing.HoldSeatsAborted as aborted:
    if isinstance(aborted.error, SeatUnavailableError):
        raise User.AddSeatsAborted(
            SeatUnavailableError(seat_ids=aborted.error.seat_ids)
        ) from None
    raise
```

## Never

- `except Seat.PlaceAborted: pass` for "already exists" tolerance — a
  timeout under load arrives as `PlaceAborted` too, and is silently
  swallowed. Check `isinstance(aborted.error, StateAlreadyConstructed)`
  and re-raise anything else.
- `except Exception:` around a Reboot call — swallows infrastructure
  failures and retries. Catch the typed `<Method>Aborted`.
- Catch only to log and continue — if the caller cannot act on it, let
  it propagate; the framework logs the typed payload.
- Write compensating undo after catching your own method's abort — a
  raised `<Method>Aborted` already rolled back that method's writes
  (`api-errors.md`).

## Limits

- An undeclared exception (a `ValueError`, a `KeyError`) inside a
  method reaches every caller as `Unknown`; the original message is
  only in the server log (1.6.0 template).
- Retryable aborts (gRPC `UNAVAILABLE`) propagate as-is so the client
  can retry transparently (1.6.0 template).
- Automatic propagation needs the outer method to declare the exact
  same class (a subclass or per-package copy does not count).

## Scales as

- Not measured.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `Propagating unhandled but declared error (in '` | An inner call's declared error passed through a method that also declares it; it is re-raised as that method's `Aborted` | Nothing, if intended; catch it to add context |
| `Unhandled (in '` … `propagating as 'Unknown'` | An error neither method declared reached the boundary | Declare it on the outer method, or catch and translate |

## See also

- [`api-errors.md`](api-errors.md) — declaring and raising typed errors
- [`rpc-refs.md`](rpc-refs.md) — probing existence via `StateNotConstructed`
- [`react-generated-client.md`](react-generated-client.md) — errors in the browser
