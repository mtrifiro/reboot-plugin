---
title: Make Constructor and `initialize` Calls Idempotent
impact: MEDIUM
impactDescription: Non-idempotent setup duplicates state on restart; a replayed call's response describes its first run; one uncertain mutation blocks every later bare mutation from that context
tags: patterns, idempotency, initialize, constructor, restart, IdempotencyUncertainError, idempotently, alias, replay, memoized
summary: "Replayed calls return the first run's response; what `IdempotencyUncertainError` means, when retries need keys, idempotent `create`/`initialize`."
step: any
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: ""
---

# Make Constructor and `initialize` Calls Idempotent

## When you are here

A mutation may run more than once (`initialize` every boot, your own
retry, a test reusing a context after a failed call) and must change
state once. How `initialize` keys calls and why a migration needs a new
alias: `lifecycle-initialize-hook.md`; clock and random values:
`patterns-time-and-randomness.md`.

## Do this

### Creation: let the persisted key do it

```python
async def initialize(context: InitializeContext):
    # Create-once: idempotent on subsequent boots (reboot-bank example).
    await Bank.create(context, SINGLETON_BANK_ID)
```

Each call in `initialize` has a persisted idempotency key: the first
boot executes it, later boots get the stored result. Outside such a
key, an explicit constructor on an existing actor raises
`StateAlreadyConstructed` (`servicer-constructor.md`).

### First-write setup in a type with no factory

A factory-less type is constructed by its first writer call; gate
set-once fields on `context.constructor`, `True` for that call only.
Inside a `factory=True` constructor it is always `True`, so it gates
nothing there (1.6.0 source).

```python
async def send(
    self, context: WriterContext, request: ChatRoom.SendRequest,
) -> None:
    if context.constructor:
        self.state.created_at = now()
    self.state.messages.append(request.message)
```

### Retrying a mutation yourself: give it a key

Any hand-written retry, and any mutation after a canceled or
transport-failed one, carries `.idempotently("alias")` or `key=`:

```python
await TaskList.ref(list_id).idempotently("Add the first task").add_task(
    context, title="Milk",
)
```

Reusing an alias means "same logical mutation": right for a retry,
wrong for two different additions.

### Uncertain mutations: what `IdempotencyUncertainError` means

A failed mutation is known not to have happened only if the exception
is an `Aborted` carrying an error the method _declared_. Anything else
(transport failure, cancellation, undeclared or framework error such
as an authorization denial) marks the context **uncertain**, and its
next mutation _without_ an idempotency key fails:

> Because we don't know if the mutation from calling `X` of state
> `'…'` failed or succeeded AND you've made some NON-IDEMPOTENT
> mutations we can't reliably determine whether or not the call to
> `Y` … is due to a retry which may cause an undesired mutation

`Y` is refused because an _earlier_ call left the context uncertain.

- **Asserting a declared error is free:**
  `with self.assertRaises(TaskList.AddTaskAborted)` on a method
  declaring `QuotaExceededError` creates no uncertainty.
- **Asserting a denial costs an alias:** `PermissionDenied` is
  undeclared, so the second denied mutation from one context fails
  (cineloop-42, 1.4.1). Give each its own
  `.idempotently("patron tries to reset the chain")`, or use a fresh
  context per assertion (`testing-harness.md`).

### Insertable records: UUIDv7 for time order

`OrderedMap` keys that should iterate in insertion order use UUIDv7
(`from uuid7 import create as uuid7`; `key=str(uuid7())`), not UUIDv4
(`stdlib-ordered-map.md`).

## Never

- A seed that opts out of the key and is not idempotent itself, e.g.
  `await bank.always().add_account(context, ...)` in `initialize` — runs
  every boot, adding the account again. Keep seeds keyed, or make the
  method a no-op once done.
- Branching on the response of a replayed call — it returns the first
  run's stored response without running the body, so counts, `created`
  flags and timestamps describe the first run (reboot-air-141-22,
  1.4.1: a startup log claimed 540 new flights every boot when 180
  were new). Ask a reader what is new.
- An alias built from a timestamp or fresh uuid — a new key each time,
  never recognized as a repeat.
- One alias for two different mutations — the second returns the
  first's result, or raises `is being reused _unsafely_` if it targets
  a different actor or method (`lifecycle-initialize-hook.md`).

## Limits

- An alias must be unique within the lifetime of its context.
- Reboot may retry transactions internally, and dev effect validation
  runs every writer and transaction body twice, committing only the
  second; the same input must produce the same committed change.
- `.always()` skips key generation and uncertainty tracking (1.6.0
  source), so it is never replayed.

## Scales as

- Not measured.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `IdempotencyUncertainError: Because we don't know if the mutation from calling` | An earlier call from this context failed in a way the client cannot classify (often a denial) | Give this mutation an alias or key (`.idempotently("...")`), or use a fresh context |

## See also

- [`lifecycle-initialize-hook.md`](lifecycle-initialize-hook.md) — how `initialize` keys each call
- [`patterns-time-and-randomness.md`](patterns-time-and-randomness.md) — retry-safe ids and timestamps
- [`testing-harness.md`](testing-harness.md) — contexts in tests
