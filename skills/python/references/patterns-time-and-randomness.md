---
title: Time and Randomness in Method Bodies
impact: HIGH
impactDescription: A fresh id or timestamp that something later re-derives or addresses splits into two values on retry or replay; a wall-clock read in a workflow diverges on every replay
tags: patterns, time, now, clock, random, uuid, uuid4, uuid7, determinism, effect validation, replay, deadline
step: any
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: "https://docs.reboot.dev/develop/side_effects"
---

# Time and Randomness in Method Bodies

## When you are here

You need "now", a deadline, a fresh id or a random token inside a
`Writer`, `Transaction` or `Workflow`. This file says which values may
come from the clock or RNG directly and the routes for the ones that
may not. The public docs say only that development runs methods twice;
older plugin text went further ("effect validation asserts the
mutations match", "never persist a wall-clock or random value from a
writer"). The 1.6.0 source does not compare runs, so this file replaces
that rule with the narrower one below.

## Do this

### What the runtime actually does (1.6.0 source)

- **No clock or RNG on any context.** `ReaderContext`, `WriterContext`,
  `TransactionContext` and `WorkflowContext` have no `now`, `random` or
  id helper. `reboot.time.DateTimeWithTimeZone.now()` is the wall clock
  with a timezone attached, not a replayed value.
- **Effect validation retries, it does not compare.** In development a
  writer or transaction body runs, then raises `EffectValidationRetry`
  ("raised in order to abort and retry transactions"), runs again, and
  only the second run commits. Nothing compares the two runs; the
  memoize path says so in a TODO ("we don't do this for other effect
  validation"). A transient retry behaves the same way: only one
  attempt commits.
- **`at_least_once` runs its callable twice under validation and
  memoizes the second result** (`reboot/aio/memoize.py`; reboot-crm-04).
  `effect_validation=EffectValidation.DISABLED` on that one call turns it
  off.

### The rule: observed values are free, addressed values are derived

| The value is… | In a Writer / Transaction | In a Workflow |
| --- | --- | --- |
| Only displayed or compared (deadline, `created_at`, display token) | Read the clock / RNG directly | Capture once via `at_least_once` |
| Addressed or re-derived later (actor id, idempotency key, foreign key, confirmation code a user quotes back) | Derive it deterministically | Derive it deterministically |
| A `when=` on `schedule(...)` | Wall clock is fine (timing is not replay-validated) | Wall clock is fine |

A stored `hold_expires_at = now + 120 s` is fine in a writer: whichever
attempt commits, the stored value is consistent with itself
(cineloop-06, 1.4.1; reboot-air-150-05 and student-system-08 saw no
validation failure across 13 and 11 tests at 1.5.0). An order id from
`uuid4()` is not: if the *caller* retries the whole call after losing
the response, a second id creates a second actor.

### Three escape routes for addressed values, in order of preference

**1. Push it into the request.** The outermost caller supplies the
value, fixed across retries. Inside a transaction-to-writer chain the
transaction reads the clock once and passes it down as a request field
(showtime-11, showtime-46):

```python
async def checkout(
    self, context: TransactionContext, request: User.CheckoutRequest,
) -> User.CheckoutResponse:
    # The browser generated request.order_id once; a retried request
    # carries the same id and re-addresses the same Order.
    await Order.ref(request.order_id).create(
        context, seat_ids=request.seat_ids,
    )
    return User.CheckoutResponse(order_id=request.order_id)
```

**2. Derive it from state you already persist.** Owner id plus a
monotonic counter, hashed if it must look opaque (cineloop-05, 1.4.1):

```python
import hashlib

def order_id(user_id: str, sequence: int) -> str:
    return hashlib.sha256(f"{user_id}:{sequence}".encode()).hexdigest()[:16]

# In the transaction:
self.state.order_count += 1
oid = order_id(context.state_id, self.state.order_count)
```

For a child `OrderedMap` or index id, derive from the owner
(`f"orders:{context.state_id}"`) and persist it into a real
`orders_index_id` field, so `rbt inspect` shows the edge and a retry
cannot allocate a second index (theater-chain-01, cineloop-05).

**3. Capture it in a `Workflow`** with `at_least_once`, at the cost of a
workflow round trip. The capture code is in `servicer-workflow-external.md`
(the `at_least_once` section).

### Route every clock read through one helper

```python
import time

def _now_ms() -> int:
    return int(time.time() * 1000)
```

Tests patch this one function with a hand-cranked fake clock, turning
a 2-minute hold test into a 2-second one (cineloop-24, 1.4.1; harness
in `testing-harness.md`).

## Never

- `seat.hold_id = str(uuid4())` in a writer when a later call
  addresses the hold by that id across a client retry — derive it or
  take it from the request.
- `datetime.now()` or `uuid4()` read directly in a workflow body — it
  differs on every replay; capture it with `at_least_once`.
- Building an `at_least_once` / `.per_workflow` alias from a timestamp
  or fresh uuid — the alias must be identical across replays.
- A test double inside `at_least_once` that pops answers off a list —
  under validation the second invocation's answer is the one kept;
  derive the stand-in's answer from its input (reboot-crm-04, 1.6.0).
- Looking for `context.now()` — it does not exist at 1.6.0 (mattprd-05
  asks for one).

## Limits

- The two runs of a validated body see different clock and RNG values;
  the committed value is the second run's.
- A 1.4.0 project reported a constructor's `uuid4()` failing
  validation and fixed it by deriving the id from the actor's own id
  (theater-network-03). The 1.6.0 source has no comparison step that
  could fail this way; the derived form is still the better shape.
- Two references disagreed on this rule (mattprd-05, team-memo-0826-07):
  `state-collections.md` and `stdlib-ordered-map.md` allocate
  `str(uuid4())` in a constructor writer, while `servicer-writer.md` and
  `scheduling-recurring.md` forbid persisting any random or wall-clock
  value from a writer. At 1.6.0 both are inside the table above: the
  constructor's id is read back from state, never re-derived.

## Scales as

- Route 1 adds one request field per value; route 3 adds a workflow
  round trip per capture.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `Re-running method` | Info, not an error: effect validation re-runs the body; the second run commits | None needed; make external calls in a workflow |
| `Re-running block with idempotency alias` | Info: an `at_least_once` callable re-runs (not `at_most_once`, not `until`); its second result is memoized | Pass `effect_validation=EffectValidation.DISABLED` on calls that must run once in dev |

## See also

- [`servicer-workflow-external.md`](servicer-workflow-external.md) — `at_least_once` capture code
- [`patterns-idempotency.md`](patterns-idempotency.md) — retry-safe creation and aliases
- [`scheduling-basic.md`](scheduling-basic.md) — deadlines that other viewers see
