---
title: Use `initialize` for First-Run Setup
impact: HIGH
impactDescription: Singletons and seeded state need an explicit creation path, and a bare call in `initialize` runs once in the application's lifetime, not once per boot
tags: initialize, InitializeContext, create, singleton, bootstrap, idempotently, alias, migration, backfill, app_internal
step: servicer
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: ""
---

# Use `initialize` for First-Run Setup

## When you are here

You need actors to exist before the first real request (a singleton,
a shared index, a catalog), or you need a one-off change applied to
state that is already persisted. `initialize` is an optional `async`
callback passed to `Application(initialize=...)`. It runs against an
`InitializeContext` each time the application starts. Each call it
makes, though, runs once in the application's lifetime. Loading a lot
of data (batching, aliases in loops, cost, test fixtures) is covered in
[`lifecycle-seeding.md`](lifecycle-seeding.md). Which API changes are
allowed on persisted state is covered in
[`api-schema-evolution.md`](api-schema-evolution.md).

## Do this

This matches the [`reboot-bank-pydantic`](https://github.com/reboot-dev/reboot-bank-pydantic) example, `backend/src/main.py`:

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

**How a call in `initialize` is keyed.** Every mutating call gets an
idempotency key. With no alias, the key comes from `(actor, method)`.
The seed behind that key is fixed per application: a constant under
`rbt dev`, and derived from the application ID on Reboot Cloud (1.6.0
source). The key is persisted. So the first boot executes the call,
and every later boot gets back the stored response without running
the body. That is what makes the `Bank.create` above safe to leave in
place. Two consequences:

- **The same method on the same actor twice** needs a distinct
  `.idempotently("alias")` (or an explicit `key=`) on each call:

  ```python
  async def initialize(context: InitializeContext):
      hello, _ = await Hello.create(
          context, "reboot-hello", initial_message="Welcome!",
      )
      # A second `send` to the same actor needs its own alias,
      # so give BOTH a distinct one.
      await hello.idempotently("Greeting").send(context, message="Hi!")
      await hello.idempotently("Follow-up").send(
          context, message="Sent after construction!",
      )
  ```

- **A migration or backfill is a new alias, not a new boot.** Changing
  the body, restarting or redeploying does not re-run a call whose key
  was already used. Give the migration a versioned alias, and bump the
  suffix to run it again:

  ```python
  async def initialize(context: InitializeContext):
      await Bank.create(context, SINGLETON_BANK_ID)
      # Runs once. Rename to "ledger-backfill-v3" to run it again.
      await Admin.ref(ADMIN_ID).idempotently(
          "ledger-backfill-v2"
      ).backfill(context)
  ```

  The alias decides *whether* the body runs. The method's own guard
  (`if self.state.sale_count > 0: return`) decides *what* it does, and
  that guard is what makes running it again safe. Have the method log
  what it found ("48 showings scanned, 11 prior sales found"). When you
  add an index or counter over data that already exists, ship this
  backfill in the same change (cineloop, 1.4.1).

  A call that has to run on **every** boot (for example, refreshing a
  config actor from code) uses `.always()`, which opts out of the key.
  The framework's own `initialize` does this for its `Application`
  singleton (1.6.0 source).

**Implicit constructor on first write.** If a type declares no
`factory=True` method, its first writer call constructs it. No
`create` is needed:

```python
async def initialize(context: InitializeContext):
    chat_room = ChatRoom.ref(EXAMPLE_STATE_MACHINE_ID)
    # Implicitly construct state machine upon first write.
    await chat_room.send(context, message="Hello, World!")
```

When the API does declare a factory (`Writer(... factory=True ...)`
or `Transaction(... factory=True ...)`), call it explicitly with
`Service.create(context, id)` or `Service.<CtorMethod>(context, id, ...)`.

**Who `initialize` is.** By default `InitializeContext` carries no
bearer token. Its caller is the application itself, so
`is_app_internal()` holds and `context.app_internal` is true in the
methods it calls. `Application(initialize_bearer_token=...)` runs the
whole hook under one bearer token instead (1.6.0 source). There is no
way to act as different users for different calls.

## Never

- **Creating singletons in a Servicer's `__init__`.** Servicer
  instances are created lazily, the first time someone references that
  actor, and there is no context there. Create singletons in
  `initialize`.

  ```python
  # DON'T
  class BankServicer(Bank.Servicer):
      def __init__(self):
          Bank.create(...)  # not at startup; no context here
  ```

- **Expecting a bare call to run again on the next boot.** Its key is
  persisted, so a backfill whose first run did nothing (because the
  data was not there yet, or a half-deployed build ran it) is marked
  done for good. You get no error, no log and no execution. The symptom
  is a method in `initialize` that produces no effect, no error and no
  log. It is not failing. It is not being called. Give it a versioned
  alias (cineloop, 1.4.1; key derivation confirmed in 1.6.0 source).
- **Trusting the response of a replayed call.** A replay returns the
  response stored from the first execution. A `created` flag or a count
  in that response describes the first boot, not this one
  (reboot-air, 1.4.1). If `initialize` needs to know what is new, ask
  through a reader.
- **Recomputing seed-time values in a migration.** For example,
  "today at 14:00" gives a different answer on the day the migration
  runs, and the actors it was first seeded into keep the old value.
  Build migration payloads from persisted state or from inputs that
  never change (showtime, 1.4.1).
- **Calling an explicit constructor a second time and expecting it to
  do nothing.** On an actor that exists, an explicit constructor aborts
  with `StateAlreadyConstructed`. A bare `create` in `initialize` is
  only safe on later boots because its persisted key replays the stored
  result before the constructor is reached.
- **A bare `.spawn()` from `initialize`.** It raises
  `IdempotencyRequiredError` (observed at 1.6.0). Write
  `ref.idempotently(alias="consumer").spawn()...`. The alias is also
  what stops each boot from starting another copy of a long-running
  loop.
- **Person-level rules applied to seeded actions.** Seeds are the
  application, never a user. A "the approver must not be the proposer"
  rule can never pass for a seed, so the method needs an explicit
  `context.app_internal` exemption with a comment saying why
  (student-system, 1.5.0). Every type that `initialize` or other actors
  call into needs `allow_if(any=[<user rule>, is_app_internal])`. Get
  this wrong and nothing fails at startup. It fails at the first call
  from that path.
- **Raising out of `initialize` and expecting the error to surface.**
  See Limits.

## Limits

- **A failing `initialize` is retried forever**, with backoff. The only
  sign is a warning line in the log. `rbt dev run` reports nothing
  else, and `Reboot().up(...)` in a test never returns, so the suite
  looks hung. The one exception is an `InputError` such as
  `IdempotencyRequiredError`, which propagates and is not retried
  (1.6.0 source).
- After a retry, the next attempt runs with a fresh context. Calls
  that already completed replay their stored results.
- With several replicas, only replica 0 runs `initialize` (1.6.0
  source).
- An `InitializeContext` holds at most one identity for the whole
  hook: either none (app-internal) or `initialize_bearer_token`.
- A key covers one `(actor, method, alias)`. Reusing one alias for a
  different actor or method is an error (see below).

## Scales as

- Every mutation in `initialize` is a full call through the runtime. In
  dev, effect validation re-runs each one. For seeds of more than a few
  dozen calls, see [`lifecycle-seeding.md`](lifecycle-seeding.md).

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `ValueError: To call '...' of '...' more than once using the same context an idempotency alias or key must be specified` | The same method was called twice on the same actor in one `initialize` | Give each call a distinct `.idempotently("alias")` |
| `ValueError: Idempotency key for ... is being reused _unsafely_` | One alias or key was used for two different calls | One alias per distinct call |
| `IdempotencyRequiredError: Calls to mutators from within your initialize function must use idempotency` | A mutation, typically a bare `.spawn()`, carried no key | `ref.idempotently(alias=...)` before the call |
| `initialize for application '...' failed with ...; will retry after backoff ...` | `initialize` raised, and it will be retried forever | Fix the exception named in the line. A hung `rbt.up()` usually means this |
| `StateAlreadyConstructed` | An explicit constructor ran on an existing actor. This was observed after an ordinary dev restart at 1.4.1, with the hook then retrying forever | Leave the bare `create` to its persisted key. If it still happens, probe with a reader before creating |

## See also

- [`lifecycle-seeding.md`](lifecycle-seeding.md): loops, batches and fixtures
- [`api-schema-evolution.md`](api-schema-evolution.md): which persisted-state changes are allowed
- [`patterns-idempotency.md`](patterns-idempotency.md): aliases, keys, uncertain mutations
