---
title: Time and Randomness in Method Bodies
impact: HIGH
impactDescription: A fresh id or timestamp that something later re-derives or addresses splits into two values on retry or replay; a wall-clock read in a workflow diverges on every replay
tags: patterns, time, now, clock, random, uuid, uuid4, uuid7, determinism, effect validation, replay, deadline
summary: "A timestamp or id that is later addressed splits on retry or replay: pass it in the request, derive it from state, or capture it with `at_least_once`."
step: any
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: "https://docs.reboot.dev/develop/side_effects"
---

# Time and Randomness in Method Bodies

## When you are here

Needing "now", a deadline, a fresh id or a random token in a `Writer`,
`Transaction` or `Workflow`. The public docs say only that development
runs methods twice. Older plugin text said "effect validation
asserts the mutations match" and "never persist a wall-clock or random
value from a writer"; the 1.6.0 source does not compare runs, so the
narrower rule below replaces that.

## Do this

### What the runtime actually does (1.6.0 source)

- **No clock or RNG on any context:** `ReaderContext`,
  `WriterContext`, `TransactionContext` and `WorkflowContext` have no
  `now`, `random` or id helper.
  `reboot.time.DateTimeWithTimeZone.now()` is the wall clock with a
  timezone, not a replayed value.
- **Effect validation retries, it does not compare:** in development a
  writer or transaction body runs, raises `EffectValidationRetry`
  ("raised in order to abort and retry transactions"), runs again, and
  only the second run commits; nothing compares them (memoize TODO:
  "we don't do this for other effect validation"). A transient retry
  likewise commits one attempt.
- **`at_least_once` runs its callable twice under validation and
  memoizes the second result** (`reboot/aio/memoize.py`; reboot-crm-04);
  `effect_validation=EffectValidation.DISABLED` on that call turns it
  off.

### The rule: observed values are free, addressed values are derived

| The value is… | In a Writer / Transaction | In a Workflow |
| --- | --- | --- |
| Only displayed or compared (deadline, `created_at`, display token) | Read the clock / RNG directly | Capture once via `at_least_once` |
| Addressed or re-derived later (actor id, idempotency key, foreign key, confirmation code a user quotes back) | Derive it deterministically | Derive it deterministically |
| A `when=` on `schedule(...)` | Wall clock is fine (timing is not replay-validated) | Wall clock is fine |

A stored `hold_expires_at = now + 120 s` is fine in a writer: whichever
attempt commits is self-consistent (cineloop-06, 1.4.1;
reboot-air-150-05 and student-system-08 saw no validation failure
across 13 and 11 tests at 1.5.0). An order id from `uuid4()` is not: a
*caller* retry after a lost response creates a second actor.

### Three escape routes for addressed values, in order of preference

**1. Push it into the request.** The outermost caller supplies it,
fixed across retries; in a transaction-to-writer chain the transaction
reads the clock once and passes it down (showtime-11, showtime-46):

```python
async def checkout(
    self, context: TransactionContext, request: User.CheckoutRequest,
) -> User.CheckoutResponse:
    # Browser minted order_id once; a retry re-addresses the same Order.
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
(`f"orders:{context.state_id}"`) and persist it in a real
`orders_index_id` field, so `rbt inspect` shows the edge and a retry
can't allocate a second index (theater-chain-01, cineloop-05).

**3. Capture it in a `Workflow`** with `at_least_once` (costs a
workflow round trip; code in `servicer-workflow-external.md`).

### Route every clock read through one helper

```python
import time

def _now_ms() -> int:
    return int(time.time() * 1000)
```

Tests patch it with a fake clock: a 2-minute hold test becomes 2
seconds (cineloop-24, 1.4.1; `testing-harness.md`).

## Never

- `seat.hold_id = str(uuid4())` in a writer when a later call
  addresses the hold by that id across a client retry — derive it or
  take it from the request.
- `datetime.now()` or `uuid4()` read directly in a workflow body — it
  differs on every replay; capture it with `at_least_once`.
- Building an `at_least_once` / `.per_workflow` alias from a timestamp
  or fresh uuid — the alias must be identical across replays.
- A test double inside `at_least_once` that pops answers off a list —
  validation keeps the second invocation's answer; derive the answer
  from its input (reboot-crm-04, 1.6.0).
- Looking for `context.now()` — it does not exist at 1.6.0 (mattprd-05
  asks for one).

## Limits

- The two runs of a validated body see different clock and RNG values;
  the committed value is the second run's.
- A 1.4.0 project saw a constructor's `uuid4()` fail validation and
  derived the id from the actor's own id (theater-network-03). 1.6.0
  has no comparison step that could fail so; the derived form is still
  better.
- `state-collections.md` and `stdlib-ordered-map.md` allocate
  `str(uuid4())` in a constructor writer while `servicer-writer.md` and
  `scheduling-recurring.md` forbid persisting random or wall-clock
  values from a writer (mattprd-05, team-memo-0826-07). At 1.6.0 both
  fit the table: the constructor's id is read back from state, never
  re-derived.

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
