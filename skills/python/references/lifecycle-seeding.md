---
title: Seed Data in Batches, Sequentially, with Aliases
impact: HIGH
impactDescription: A naive seed (one transaction per record, gathered concurrently, bare calls in a loop) hangs, stalls silently or takes minutes, and a full production seed in every test dominates the suite
tags: seeding, seed, initialize, bulk, batch, fixture, idempotently, alias, OrderedMap, entries, expunge, effect-validation
summary: "Concurrent or one-per-record seeding hangs or takes minutes; seed in sequential batched transactions with stable per-call aliases."
step: servicer
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: ""
---

# Seed Data in Batches, Sequentially, with Aliases

## When you are here

Loading a catalog, demo data or a realistic dev dataset from
`initialize` and test fixtures. Read
[`lifecycle-initialize-hook.md`](lifecycle-initialize-hook.md) first
(keying: once ever, versioned aliases for migrations, no user identity).
Stop/expunge/restart: [`../../run/SKILL.md`](../../run/SKILL.md).

## Do this

- **One function, size as parameters**: `initialize` passes production
  values, tests a fraction.
- **One transaction per batch**: it creates its actors and adds them to
  the shared index with one bulk `insert(entries=...)`.
- **Batches one at a time**, each call with an **alias built from the
  batch's contents**.

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
        # Same method on the same actor each iteration: each needs its own
        # alias; built from the ids, it lets a restarted seed skip landed batches.
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

### Demo data, in development only

A believable dataset makes every view show something the first time it
opens. Seed it only under `rbt dev`:

```python
from reboot.run_environments import running_rbt_dev


async def initialize(context: InitializeContext):
    if running_rbt_dev():  # false in tests, `rbt serve` and Reboot Cloud
        await seed_demo(context, rooms=12, guests=8)
```

`running_rbt_dev()` is true under `rbt dev run` and false under the test
harness (observed at 1.6.0); scenarios seed what each needs themselves.

Tests call the same function smaller:
`await seed_chain(self.rbt.create_external_context(name="seed", app_internal=True), theaters=2, seats_per_row=5)`.
Assert against seed constants (`LAB_SHOWINGS`), not literals (`48`).

## Never

- **Concurrent seeding transactions** (`asyncio.gather` over batches,
  `asyncio.Semaphore(12)`) — transactions sharing actors (index, parent,
  term) queue on each other's locks. Twelve concurrent bulk imports
  stalled indefinitely at 0-2% CPU, nothing logged; sequentially each
  took five to seven seconds (student-sor, 1.5.0). With no reads inside
  and a fixed lock order, four at a time still ran at one-sixth of
  sequential throughput.
- **A shared actor called in a loop without a per-iteration alias**
  (registering N theaters with one chain): e.g.
  `chain.idempotently(f"reg-{theater.id}").register_theater(...)`.
  Creating N distinct actors needs none (cineloop, 1.4.1).
- **Aliases from values that change between runs** (wall clock, random)
  — a restarted seed can't resume; use the record's id or date.
- **One transaction per record** — ~3,600 calls at ~1.5 s each in dev,
  unfinished after five minutes (student-sor, 1.5.0).
- **Hundreds of creates and one shared `OrderedMap` in one
  transaction** (Limits).
- **A big `list[Entity]` inline on an actor the seed keeps writing** —
  every write re-serializes it (8,878 records rewritten per progress
  update, client-portal). Unbounded collections go in an `OrderedMap`;
  a domain-bounded list (200 seats on one showing) can stay inline
  ([`state-collections.md`](state-collections.md)).
- **The full production seed in every test** — only in the few
  (merged) tests asserting production size; others seed the minimum
  through an `app_internal=True` context (showtime, cineloop).
- **Seeding through a user context in a test** — `initialize`-only
  methods are usually internal-only (`PermissionDenied`); use
  `rbt.create_external_context(name=..., app_internal=True)`.
- **Debugging dev state that lived through incompatible designs** —
  expunge and reseed (`lifecycle-rbtrc.md` § Never).

## Limits

- **No documented transaction size ceiling, but one is reachable**: 138
  creates plus inserts into one shared `OrderedMap` worked; 360 hung the
  app at startup, the log filling with lock waits, no error
  (reboot-air, 1.4.1). Keep batches to tens of creates.
- A per-actor lock wait gives up after 30 s and retries
  (`LOCK_ACQUIRE_DEADLINE_DEFAULT`, 1.6.0 source): an oversized or
  contended seed loops on lock waits rather than failing.
- **Seeding `User` actors has no public API**; use the semi-private
  `await UserServicer._authenticated(context, state_id=user_id)` — on
  the servicer class (`User._authenticated` doesn't exist); idempotent
  via a fixed key, safe from `initialize` (1.6.0 source).
- A seed from `initialize` can't act as a user
  ([`lifecycle-initialize-hook.md`](lifecycle-initialize-hook.md)).
- `rbt dev expunge` without `--yes` blocks forever with no terminal.
- A long seed goes quiet: the effect-validation `Re-running` line
  prints once per method, then is silenced for five minutes
  (student-sor, 1.5.0). Measure progress from state (`rbt inspect`), not
  the log.

## Scales as

- `rbt dev run`, validation on: a four-hop transaction (two reads, one
  create, one `OrderedMap` insert) ~1.5 s (student-sor, 1.5.0).
- **Effect validation roughly doubles mutation latency** (~10.6 s →
  5.7 s, ~1.9 s → 1.4 s disabled; bluesky, team memo). Large seeds:
  `rbt dev run --effect-validation=disabled` (`enabled`, `quiet`,
  `disabled`; default `quiet`); harness:
  `rbt.up(..., effect_validation=EffectValidation.DISABLED)` (1.6.0
  source). With it on, `Re-running method X.Create to validate effects`
  per seeded create is normal.
- One sequential redesign, validation disabled: 193 admits at ~one per
  second, then ~6 s per bulk student import, ~15 minutes total on an
  M-series laptop; a mid-seed restart resumed via the aliases
  (student-sor, 1.5.0).
- Harness tests have a ~2 s floor; a full production seed added ~30 s
  each. A parameterized seed cut one suite from 7m50s to 3m52s. Compare
  fixtures with `pytest --durations` on one trivial test each
  (cineloop, 1.4.1).

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `PermissionDenied` (on a seed call in a test) | Internal-only method called with a user context | Seed through `create_external_context(..., app_internal=True)` |
| `database.cc Check failed` | Dev state from an incompatible earlier design | Stop the app, run `rbt dev expunge --application-name=<name> --yes`, reseed |
| `is presumed deadlocked with it; aborting so that the older transaction proceeds` | Concurrent transactions contending for the same actors; at 1.6.0 also every sequential `initialize` transaction against its own previous run, about 2.5 s each, then succeeding | Seed sequentially, through bulk methods (one transaction per record group) |

## See also

- [`lifecycle-initialize-hook.md`](lifecycle-initialize-hook.md): how calls in `initialize` are keyed
- [`stdlib-ordered-map.md`](stdlib-ordered-map.md): bulk `insert(entries=...)`
- [`testing-harness.md`](testing-harness.md): fixtures and `app_internal=True`
