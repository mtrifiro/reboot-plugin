---
title: Error Handling Patterns
impact: MEDIUM
impactDescription: Inconsistent error handling makes failures opaque to callers
tags: patterns, errors, MethodAborted, catch, propagate, SystemAborted, timeout
summary: "`<Method>Aborted` also carries timeouts and system errors: inspect `.error`, re-raise the rest; typed errors across actors."
step: any
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: ""
---

# Error Handling Patterns

## When you are here

Calling a method that can abort (servicer, workflow, test) and
deciding what to catch, what to let through, and how a nested typed
error reaches your caller. Declaring and raising errors:
[`api-errors.md`](api-errors.md).

## Do this

Catch `<Method>Aborted`, branch on the type of `.error`, re-raise the
rest:

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

`.error` is the union of the method's declared error `Model`s **plus**
every gRPC error (`DeadlineExceeded`, `Unavailable`, `Unknown`, …) and
every Reboot error (`StateNotConstructed`, `StateAlreadyConstructed`,
…) (1.6.0 source, `reboot/aio/aborted.py`), so the `isinstance` check
is required.

Typed errors are the UI contract: `SeatUnavailableError(seat_ids=[...])`
lets it say "F-11 and F-12 were just taken" and repaint them; a generic
exception collapses to "something went wrong" (observed at 1.4.1).

### Carrying a typed error across an actor boundary

If `User.add_seats` calls `Showing.hold_seats` and both declare the
**same** `SeatUnavailableError` class, an uncaught inner abort is
re-raised as `User.AddSeatsAborted` with the payload intact, logging
`Propagating unhandled but declared error` (1.6.0 template); otherwise
the caller gets `Unknown`. At 1.4.1 the payload arrived empty. To be
sure, or when the classes differ, re-raise explicitly:

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
  timeout under load is also `PlaceAborted` and gets swallowed; check
  `isinstance(aborted.error, StateAlreadyConstructed)`, re-raise the rest.
- `except Exception:` around a Reboot call — swallows infrastructure
  failures and retries; catch the typed `<Method>Aborted`.
- Catch only to log and continue — let it propagate; the framework logs
  the typed payload.
- Write compensating undo after catching your own method's abort — a
  raised `<Method>Aborted` already rolled back its writes
  (`api-errors.md`).

## Limits

- An undeclared exception (`ValueError`, `KeyError`) reaches callers as
  `Unknown`; the message is only in the server log (1.6.0 template).
- Retryable aborts (gRPC `UNAVAILABLE`) propagate as-is so the client
  retries transparently (1.6.0 template).
- Automatic propagation needs the exact same class on the outer method
  (not a subclass or per-package copy).

## Scales as

- Not measured.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `Propagating unhandled but declared error (in '` | An inner call's declared error passed through a method that also declares it; it is re-raised as that method's `Aborted` | Nothing, if intended; catch it to add context |

## See also

- [`api-errors.md`](api-errors.md) — declaring and raising typed errors
- [`rpc-refs.md`](rpc-refs.md) — probing existence via `StateNotConstructed`
- [`react-generated-client.md`](react-generated-client.md) — errors in the browser
