---
title: Seed Data in Batches, Sequentially, with Aliases
impact: HIGH
impactDescription: A naive seed (one transaction per record, gathered concurrently, bare calls in a loop) hangs, stalls silently or takes minutes, and a full production seed in every test dominates the suite
tags: seeding, seed, initialize, bulk, batch, fixture, idempotently, alias, OrderedMap, entries, expunge, effect-validation
step: servicer
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: ""
---

# Seed Data in Batches, Sequentially, with Aliases

## When you are here

You are writing the code that loads a catalog, demo data or a
realistic development dataset, called from `initialize` and from test
fixtures. How a call in `initialize` is keyed (once ever, versioned
aliases for migrations, no user identity) is covered in
[`lifecycle-initialize-hook.md`](lifecycle-initialize-hook.md). Read
that first. Stopping, expunging and restarting a dev app is covered in
[`../../run/SKILL.md`](../../run/SKILL.md).

## Do this

Write the seed as **one function with its size as parameters**.
`initialize` calls it with production values, and tests call it with
a fraction. Each **batch is one transaction**: it creates its actors
and adds them to the shared index with one bulk `insert(entries=...)`.
Batches run **one at a time**, and each call carries an **alias built
from what that batch contains**.

`backend/src/seed.py`:

```python
from reboot.aio.external import ExternalContext
from chain.v1.chain_rbt import Chain

CHAIN_ID = "chain"


async def seed_chain(
    context: ExternalContext,
    *,
    theaters: int,
    seats_per_row: int,
    batch_size: int = 20,
) -> None:
    await Chain.create(context, CHAIN_ID)
    chain = Chain.ref(CHAIN_ID)
    ids = [f"theater-{n:03d}" for n in range(theaters)]
    for start in range(0, len(ids), batch_size):
        batch = ids[start:start + batch_size]
        # Same method, same actor, every iteration: each call needs
        # its own alias. Built from the batch's ids, it also lets a
        # restarted seed skip the batches that already landed.
        await chain.idempotently(f"add-theaters-{batch[0]}").add_theaters(
            context, theater_ids=batch, seats_per_row=seats_per_row,
        )
```

`backend/src/main.py`:

```python
async def initialize(context: InitializeContext):
    await seed_chain(context, theaters=12, seats_per_row=20)
```

The batch transaction in `ChainServicer`:

```python
from reboot.std.collections.ordered_map.v1.ordered_map import OrderedMap
from reboot.std.item.v1.item import Item


async def add_theaters(
    self, context: TransactionContext, request: Chain.AddTheatersRequest,
) -> None:
    for theater_id in request.theater_ids:
        # Distinct actors: no alias needed.
        await Theater.create(
            context, theater_id, seats_per_row=request.seats_per_row,
        )
    # One bulk insert per batch, not one insert per theater.
    await OrderedMap.ref(self.state.theater_index_id).insert(
        context,
        entries={tid: Item(bytes=tid.encode()) for tid in request.theater_ids},
    )
```

In a test, call the same function with less data:
`await seed_chain(self.rbt.create_external_context(name="seed", app_internal=True), theaters=2, seats_per_row=5)`.
Assert against seed constants, not literals: `LAB_SHOWINGS`, not `48`.

## Never

- **Concurrent seeding transactions** (`asyncio.gather` over batches,
  `asyncio.Semaphore(12)`). If the transactions share actors (an
  index, a parent, a term), they queue on each other's locks. Twelve
  concurrent bulk imports stalled indefinitely at 0-2% CPU, with no
  error, retry or timeout in the log. The same imports run one at a
  time took five to seven seconds each (student-sor, 1.5.0). Even with
  no reads inside the transaction and a fixed lock order, four at a
  time ran at one-sixth of sequential throughput. Seed sequentially.
- **A loop that calls a shared actor without an alias per
  iteration.** A loop that creates N actors needs no alias, because
  each call goes to a different actor. A loop that registers each one
  with a shared chain or index calls the same method on the same actor
  N times. Each of those calls needs a distinct alias, such as
  `chain.idempotently(f"reg-{theater.id}").register_theater(...)`
  (cineloop, 1.4.1).
- **Aliases built from anything that changes between runs** (wall
  clock, a random value). The alias is what lets a restarted seed
  resume correctly. Build it from the record's id or date.
- **One transaction per record.** Roughly 3,600 calls at about 1.5 s
  each in dev made a seed that had not finished after five minutes
  (student-sor, 1.5.0). Batch the records into one transaction per
  parent, with bulk `entries=` inserts.
- **Hundreds of creates and one shared `OrderedMap` in a single
  transaction.** See Limits. Split it into batches.
- **A big `list[Entity]` held inline on an actor the seed keeps
  writing.** Every write re-serialises the whole actor. One actor held
  8,878 records and re-wrote all of them for each progress update
  (client-portal). Put an unbounded collection in an `OrderedMap`. A
  list bounded by the domain (200 seats on one showing) can stay
  inline. See [`state-collections.md`](state-collections.md).
- **The full production seed in every test.** Keep it for the few
  tests whose assertion is the production size, and merge those tests.
  Every other test seeds the minimum it asserts on, through an
  `app_internal=True` context (showtime, cineloop).
- **Seeding through a user context in a test.** A method that only
  `initialize` calls is usually internal-only, so a user context gets
  `PermissionDenied`. Use
  `rbt.create_external_context(name=..., app_internal=True)`. This is
  the test-side equivalent of `initialize`.
- **Debugging dev state that has lived through incompatible designs**
  (method kinds changed, scheduled tasks pointing at reworked methods).
  Stop the app, run
  `rbt dev expunge --application-name=<name> --yes` and reseed
  (theater-network, 1.4.0). Never expunge while `rbt dev run` is still
  running. Reload every open browser tab afterwards.

## Limits

- **No documented transaction size ceiling, but one is reachable.**
  One transaction creating 138 actors and inserting them into one
  shared `OrderedMap` worked. The same transaction with 360 hung the
  app at startup, and the log filled with lock waits instead of an
  error (reboot-air, 1.4.1). Keep each batch to tens of creates.
- A per-actor lock wait gives up after 30 s and is retried
  (`LOCK_ACQUIRE_DEADLINE_DEFAULT`, 1.6.0 source). So an oversized or
  contended seed shows as a loop of lock waits, not a failure.
- **Seeding `User` actors has no public API.** The only path is the
  semi-private
  `await UserServicer._authenticated(context, state_id=user_id)`. It
  is on the servicer class, not the state type (`User._authenticated`
  does not exist), and it constructs the user idempotently through a
  fixed key, so it is safe to call from `initialize` (1.6.0 source).
- A seed run from `initialize` cannot act as a user. See
  [`lifecycle-initialize-hook.md`](lifecycle-initialize-hook.md).
- `rbt dev expunge` without `--yes` waits for confirmation. With no
  terminal attached, it blocks forever.

## Scales as

- In `rbt dev run`, a four-hop transaction (two reads, one create, one
  `OrderedMap` insert) took about 1.5 s with effect validation on
  (student-sor, 1.5.0).
- **Effect validation roughly doubles mutation latency.** One
  measurement went from about 10.6 s to 5.7 s, and another from about
  1.9 s to 1.4 s (bluesky, team memo). For a large seed, start the app
  with `rbt dev run --effect-validation=disabled`. The choices are
  `enabled`, `quiet` and `disabled`, and the default is `quiet`. In
  the harness, use
  `rbt.up(..., effect_validation=EffectValidation.DISABLED)` (1.6.0
  source). With validation on, a log line saying
  `Re-running method X.Create to validate effects` for each seeded
  create is normal.
- One measured redesign, sequential and with validation disabled: 193
  admits at about one per second, then about 6 s per bulk student
  import. That came to about 15 minutes end to end on an M-series
  laptop. A restart mid-seed resumed correctly through the aliases
  (student-sor, 1.5.0).
- In tests, each harness test has a floor of about 2 s even with
  nothing seeded. A full production seed added about 30 s per test.
  Switching to a parameterised seed took one suite from 7m50s to 3m52s.
  To compare fixtures, run `pytest --durations` on one trivial test
  per fixture (cineloop, 1.4.1).

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `StateNotConstructed { requires_constructor: true }` | A test called into an actor that production's `initialize` constructs, but the test fixture did not | Construct it in the fixture, or pass the production `initialize=` to `rbt.up(...)` |
| `PermissionDenied` (on a seed call in a test) | An internal-only method was called with a user context | Seed through `create_external_context(..., app_internal=True)` |
| `ValueError: To call '...' of '...' more than once using the same context an idempotency alias or key must be specified` | A loop called the same method on a shared actor without an alias per iteration | Add `.idempotently(f"...-{id}")` |
| `database.cc Check failed` | Dev state from an incompatible earlier design | Stop the app, run `rbt dev expunge --application-name=<name> --yes`, reseed |
| `is presumed deadlocked with it; aborting so that the older transaction proceeds` | Concurrent transactions are contending for the same actors | Seed sequentially |

## See also

- [`lifecycle-initialize-hook.md`](lifecycle-initialize-hook.md): how calls in `initialize` are keyed
- [`stdlib-ordered-map.md`](stdlib-ordered-map.md): bulk `insert(entries=...)`
- [`testing-harness.md`](testing-harness.md): fixtures and `app_internal=True`
