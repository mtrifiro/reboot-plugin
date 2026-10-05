---
title: Use `initialize` for First-Run Setup
impact: HIGH
impactDescription: Singletons and seeded state need an explicit creation path, and a bare call in `initialize` runs once in the application's lifetime, not once per boot
tags: initialize, InitializeContext, create, singleton, bootstrap, idempotently, alias, migration, backfill, app_internal
summary: "Each `initialize` call runs once per app lifetime, not per boot; migrations need new aliases; failures retry forever."
step: servicer
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: ""
---

# Use `initialize` for First-Run Setup

## When you are here

Actors must exist before the first request (singleton, shared index,
catalog), or persisted state needs a one-off change.
`Application(initialize=...)` takes an optional `async` callback run
with an `InitializeContext` on every start; each call it makes runs once
in the application's lifetime. Bulk loading (batching, aliases in loops, cost, fixtures):
[`lifecycle-seeding.md`](lifecycle-seeding.md). Allowed changes to
persisted state: [`api-schema-evolution.md`](api-schema-evolution.md).

## Do this

From [`reboot-bank-pydantic`](https://github.com/reboot-dev/reboot-bank-pydantic) `backend/src/main.py`:

```python
from reboot.aio.applications import Application
from reboot.aio.external import InitializeContext
from bank.v1.bank_rbt import Bank

SINGLETON_BANK_ID = 'SVB'


async def initialize(context: InitializeContext):
    await Bank.create(context, SINGLETON_BANK_ID)


async def main():
    await Application(
        servicers=[AccountServicer, BankServicer],
        initialize=initialize,
    ).run()
```

**Keying.** Every mutating call gets a persisted idempotency key, from
`(actor, method)` with no alias, seeded per application (a constant
under `rbt dev`, the application ID on Reboot Cloud; 1.6.0 source). The
first boot executes; later boots return the stored response without
running the body, so the `Bank.create` above is safe to leave. Hence:

- **Same method on the same actor twice**: give BOTH calls a distinct
  `.idempotently("alias")` (or explicit `key=`):
  `await hello.idempotently("Greeting").send(context, message="Hi!")`,
  then `hello.idempotently("Follow-up").send(...)`.

- **A migration or backfill is a new alias, not a new boot.** Editing
  the body, restarting or redeploying never re-runs a used key — a
  backfill whose first run did nothing (data not there yet, or a
  half-deployed build ran it) is done for good: no effect, no error, no
  log; it isn't failing, it isn't called (cineloop, 1.4.1; key
  derivation confirmed in 1.6.0 source). Use a versioned alias; bump the
  suffix to run again:

  ```python
  async def initialize(context: InitializeContext):
      await Bank.create(context, SINGLETON_BANK_ID)
      # Runs once. Rename to "ledger-backfill-v3" to run it again.
      await Admin.ref(ADMIN_ID).idempotently(
          "ledger-backfill-v2"
      ).backfill(context)
  ```

  The alias decides *whether* the body runs; the method's guard
  (`if self.state.sale_count > 0: return`) decides *what* it does and
  makes re-running safe. Log what it found ("48 showings scanned, 11
  prior sales found"). Ship a new index or counter over existing data
  with its backfill in the same change (cineloop, 1.4.1).

- **Every boot** (e.g. refreshing a config actor from code):
  `.always()` opts out of the key, as the framework's own `initialize`
  does for its `Application` singleton (1.6.0 source).

**Implicit constructor on first write.** A type with no `factory=True`
method is constructed by its first writer call, no `create` needed:
`await ChatRoom.ref(EXAMPLE_STATE_MACHINE_ID).send(context, message="Hello, World!")`.
With a declared factory (`Writer(... factory=True ...)` or
`Transaction(... factory=True ...)`), call `Service.create(context, id)`
or `Service.<CtorMethod>(context, id, ...)` explicitly.

**Identity.** By default no bearer token: the caller is the application,
so `is_app_internal()` holds and `context.app_internal` is true in
called methods. `Application(initialize_bearer_token=...)` runs the
whole hook under one token instead (1.6.0 source).

## Never

- **Creating singletons in a Servicer's `__init__`** (`Bank.create(...)`
  there) — Servicers are created lazily on first reference, with no
  context.
- **Expecting a bare call to run again next boot** — use a versioned
  alias (above).
- **Trusting a replayed call's response** — it describes the first
  boot; ask a reader what is new (`patterns-idempotency.md` § Never).
- **Recomputing seed-time values in a migration.** "Today at 14:00"
  differs on migration day while seeded actors keep the old value.
  Build payloads from persisted state or never-changing inputs
  (showtime, 1.4.1).
- **Calling an explicit constructor again expecting a no-op**
  (`rpc-constructor-calls.md` § Never). A bare `create` in `initialize`
  is safe on later boots only because its persisted key replays first.
- **A bare `.spawn()` from `initialize`.** It raises
  `IdempotencyRequiredError` (observed at 1.6.0). Write
  `ref.idempotently(alias="consumer").spawn()...`; the alias also stops
  each boot starting another copy of a long-running loop.
- **Person-level rules on seeded actions.** Seeds are the application,
  so "the approver must not be the proposer" never passes; add an
  explicit `context.app_internal` exemption with a why-comment
  (student-system, 1.5.0). Every type `initialize` or other actors call
  needs `allow_if(any=[<user rule>, is_app_internal])`; a miss fails at
  the first call from that path, not at startup.
- **Raising out of `initialize` expecting the error to surface**
  (Limits).

## Limits

- **A failing `initialize` is retried forever** with backoff; the only
  sign is a log warning, and `Reboot().up(...)` never returns, so the
  suite looks hung. Exception: an `InputError` such as
  `IdempotencyRequiredError` propagates, not retried (1.6.0 source).
- A retry gets a fresh context; completed calls replay stored results.
- With several replicas, only replica 0 runs `initialize` (1.6.0 source).
- One identity for the whole hook: none (app-internal) or
  `initialize_bearer_token`; no per-call users.
- A key covers one `(actor, method, alias)`; reusing an alias for a
  different actor or method is an error (below).

## Scales as

- Each mutation is a full runtime call, re-run by dev effect
  validation; seeds over a few dozen calls:
  [`lifecycle-seeding.md`](lifecycle-seeding.md).

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `ValueError: To call '...' of '...' more than once using the same context an idempotency alias or key must be specified` | Same method called twice on one actor in `initialize` (e.g. a seeding loop on a shared actor) | Distinct `.idempotently("alias")` per call; in a loop `.idempotently(f"...-{id}")` |
| `ValueError: Idempotency key for ... is being reused _unsafely_` | One alias or key used for two different calls | One alias per distinct call |
| `IdempotencyRequiredError: Calls to mutators from within your initialize function must use idempotency` | A mutation, typically a bare `.spawn()`, had no key | `ref.idempotently(alias=...)` before the call |
| `initialize for application '...' failed with ...; will retry after backoff ...` | `initialize` raised; retried forever. Usually why `rbt.up()` hangs | Fix the named exception |
| `StateAlreadyConstructed` | Explicit constructor on an existing actor; observed after an ordinary dev restart at 1.4.1, the hook then retrying forever | Leave the bare `create` to its persisted key; if it persists, probe with a reader before creating |

## See also

- [`lifecycle-seeding.md`](lifecycle-seeding.md): loops, batches and fixtures
- [`api-schema-evolution.md`](api-schema-evolution.md): which persisted-state changes are allowed
- [`patterns-idempotency.md`](patterns-idempotency.md): aliases, keys, uncertain mutations
