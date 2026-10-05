---
title: Make Constructor and `initialize` Calls Idempotent
impact: MEDIUM
impactDescription: Non-idempotent setup duplicates state on restart; a replayed call's response describes its first run; one uncertain mutation blocks every later bare mutation from that context
tags: patterns, idempotency, initialize, constructor, restart, IdempotencyUncertainError, idempotently, alias, replay, memoized
summary: "What `IdempotencyUncertainError` means and when a retry needs an idempotency key; replayed calls return the first run's response; idempotent `create` / `initialize`; UUIDv7 for insertable records."
step: tests
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: ""
---

# Make Constructor and `initialize` Calls Idempotent

## When you are here

A mutation may run more than once (`initialize` on every boot, your
own retry, a test that keeps using a context after a failed call) and
must change state once. How `initialize` keys each call, and why a
migration needs a new alias, is in `lifecycle-initialize-hook.md`;
clock and random values in method bodies are in
`patterns-time-and-randomness.md`.

## Do this

### Creation: let the persisted key do it

```python
async def initialize(context: InitializeContext):
    # Create-once: idempotent on subsequent boots (reboot-bank example).
    await Bank.create(context, SINGLETON_BANK_ID)
```

The `initialize` hook runs on every boot, but each call in it has a
persisted idempotency key: the first boot executes it, later boots get
the stored result without running the constructor. Outside such a key,
an explicit constructor called a second time on an existing actor
raises `StateAlreadyConstructed` (`servicer-constructor.md`).

### First-write setup in a type with no factory

A factory-less type is constructed by its first writer call; gate
set-once fields on `context.constructor`, which is `True` for that one
call only. Inside an explicit `factory=True` constructor it is always
`True` (the body never runs on an existing actor), so it gates nothing
there (1.6.0 source).

```python
async def send(
    self, context: WriterContext, request: ChatRoom.SendRequest,
) -> None:
    if context.constructor:
        self.state.created_at = now()
    self.state.messages.append(request.message)
```

### Retrying a mutation yourself: give it a key

Any hand-written retry loop, and any mutation issued after a
cancelled or transport-failed one, carries `.idempotently("alias")` or
an explicit `key=`:

```python
await TaskList.ref(list_id).idempotently("Add the first task").add_task(
    context, title="Milk",
)
```

Reusing an alias tells Reboot "this is the same logical mutation":
exactly right for a retry, exactly wrong for two different additions.

### Uncertain mutations: what `IdempotencyUncertainError` means

When a mutation call raises, the client can only be sure it did not
happen if the exception is **definitively from the backend**: an
`Aborted` carrying an error the method _declared_. Anything else (a
transport failure, a cancellation, an undeclared or framework error
such as an authorization denial) leaves it unable to tell, so it marks
the context as having an **uncertain mutation**. The next mutation
from that context _without_ an idempotency key then fails:

> Because we don't know if the mutation from calling `X` of state
> `'…'` failed or succeeded AND you've made some NON-IDEMPOTENT
> mutations we can't reliably determine whether or not the call to
> `Y` … is due to a retry which may cause an undesired mutation

It refuses `Y` because an _earlier_ call left the context uncertain.

- **Asserting a declared error is free.** `with
  self.assertRaises(TaskList.AddTaskAborted)` on a method that declares
  `QuotaExceededError` creates no uncertainty.
- **Asserting a denial costs an alias.** `PermissionDenied` is not
  declared, so the second denied mutation from one context fails as
  above (cineloop-42, 1.4.1). Give each denied mutation its own
  `.idempotently("patron tries to reset the chain")`, or use a fresh
  context per assertion (`testing-harness.md`).

### Insertable records: UUIDv7 for time order

Keys of an `OrderedMap` that should iterate in insertion order use
UUIDv7, not UUIDv4:

```python
from uuid7 import create as uuid7

await OrderedMap.ref(self.state.account_ids_map_id).insert(
    context,
    key=str(uuid7()),
    bytes=account_id.encode(),
)
```

## Never

- A seed that opts out of the key and is not idempotent itself, e.g.
  `await bank.always().add_account(context, ...)` in `initialize`: it
  runs on every boot and adds the account again. Leave seed calls
  keyed, or make the method a no-op when its work is done.
- Branching on the response of a replayed call. A replayed idempotent
  call returns the stored response from its first execution and the
  body does not run, so counts, `created` flags and timestamps in it
  describe the first run (reboot-air-141-22, 1.4.1: a startup log
  claimed 540 new flights every boot when 180 were new). Ask a reader
  what is new.
- An alias built from a timestamp or fresh uuid — a new key each time,
  so the call is never recognised as a repeat.
- One alias for two different mutations — the second returns the
  first's result, or raises `is being reused _unsafely_` if it targets
  a different actor or method (`lifecycle-initialize-hook.md`).

## Limits

- An alias must be unique within the lifetime of its context.
- Reboot may retry transactions internally, and in dev effect
  validation runs every writer and transaction body twice, committing
  only the second run. Code must not depend on running exactly once:
  the same input must produce the same state change once committed.
- `.always()` skips key generation and uncertainty tracking entirely
  (1.6.0 source), so it is never replayed.

## Scales as

- Not measured.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `IdempotencyUncertainError: Because we don't know if the mutation from calling` | An earlier call from this context failed in a way the client cannot classify | Give this mutation an alias or key, or use a fresh context |
| `aborted with 'StateAlreadyConstructed'` | An explicit constructor ran on an existing actor outside a used key | Leave creation to `initialize`'s key, or get-or-create (`rpc-constructor-calls.md`) |

## See also

- [`lifecycle-initialize-hook.md`](lifecycle-initialize-hook.md) — how `initialize` keys each call
- [`patterns-time-and-randomness.md`](patterns-time-and-randomness.md) — retry-safe ids and timestamps
- [`testing-harness.md`](testing-harness.md) — contexts in tests
