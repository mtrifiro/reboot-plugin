---
title: Time and Randomness in Method Bodies
impact: MEDIUM
impactDescription: A writer or transaction may store a clock or random value; a workflow body that reads one directly diverges on every replay
tags: patterns, time, now, clock, random, uuid, uuid4, uuid7, determinism, effect validation, replay, deadline
summary: "Writers and transactions may store `uuid4()` or the time; in a workflow, read them inside `at_least_once`."
step: servicer
applies: [mcp-ui, web-app, backend-only]
always: false
when: "a method reads the clock or random values"
verified: 1.6.0
docs: "https://docs.reboot.dev/learn_more/side_effects/"
---

# Time and Randomness in Method Bodies

## When you are here

Needing "now", a deadline, a fresh id or a random token in a `Writer`,
`Transaction` or `Workflow`. The public docs say only that development
runs methods twice. Older plugin text said "effect validation asserts
the mutations match" and "never persist a wall-clock or random value
from a writer". The 1.6.0 source does not compare runs, and Reboot's
own skills now say values that differ between runs are fine to store,
so that rule is gone.

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
- **A caller's retry is covered by idempotency:** a retry with the same
  idempotency key gets the first call's response back, the stored id
  included; a call without one is a new call and gets a new result
  (`patterns-idempotency.md`).
- **`at_least_once` runs its callable twice under validation and
  memoizes the second result** (`reboot/aio/memoize.py`; reboot-crm-04);
  `effect_validation=EffectValidation.DISABLED` on that call turns it
  off.

### The rule

| Where | Clock or random value |
| --- | --- |
| `Writer` / `Transaction` body | Read it directly and store it: `created_at`, a deadline, an order id from `uuid4()` |
| `Workflow` body | Read it inside `at_least_once`, never directly: the body re-runs on every replay |
| `when=` on `schedule(...)` | Wall clock is fine |

```python
async def checkout(
    self, context: TransactionContext, request: User.CheckoutRequest,
) -> User.CheckoutResponse:
    order_id = str(uuid4())
    await Order.ref(order_id).create(context, seat_ids=request.seat_ids)
    self.state.order_ids.append(order_id)
    return User.CheckoutResponse(order_id=order_id)
```

A value is only wrong where something computes it again instead of
reading it back: a second call that re-mints the id, or a workflow body
outside a memoized step.

### When several writers must agree, read it once

A transaction that calls two writers on different actors, each needing
the same timestamp or id, reads it once and passes it down as a request
field (showtime-11, showtime-46). Each writer reading its own clock
gets its own value.

### Route every clock read through one helper

```python
import time

def _now_ms() -> int:
    return int(time.time() * 1000)
```

Tests patch it with a fake clock: a 2-minute hold test becomes 2
seconds (cineloop-24, 1.4.1; `testing-harness.md`).

## Never

- `datetime.now()` or `uuid4()` read directly in a workflow body: it
  differs on every replay; capture it with `at_least_once`.
- Building an `at_least_once` / `.per_workflow` alias from a timestamp
  or fresh uuid: the alias must be identical across replays.
- A test double inside `at_least_once` that pops answers off a list:
  validation keeps the second invocation's answer; derive the answer
  from its input (reboot-crm-04, 1.6.0).
- Looking for `context.now()`: it does not exist at 1.6.0 (mattprd-05
  asks for one).

## Limits

- The two runs of a validated body see different clock and RNG values;
  the committed value is the second run's.
- A 1.4.0 project saw a constructor's `uuid4()` fail validation and
  derived the id from the actor's own id (theater-network-03). 1.6.0
  has no comparison step that could fail so.

## Scales as

- Reading once and passing down adds one request field per shared
  value; an `at_least_once` capture adds a workflow round trip.

## Errors you will see

`Re-running method`: see `servicer-writer.md`; `Re-running block with idempotency alias`: see `servicer-workflow-external.md`.

## See also

- [`servicer-workflow-external.md`](servicer-workflow-external.md), `at_least_once` capture code
- [`patterns-idempotency.md`](patterns-idempotency.md), retry-safe calls and aliases
- [`scheduling-basic.md`](scheduling-basic.md), deadlines that other viewers see
