---
title: Load, Cost and Benchmarking
impact: HIGH
impactDescription: Unmeasured designs put a transaction or a fan-out on a click path and ship a page that takes seconds
tags: patterns, cost, performance, benchmark, load test, effect validation, transaction, forall, subscriptions
step: any
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: ""
---

# Load, Cost and Benchmarking

## When you are here

You are choosing a method kind or an actor boundary for a path that
must feel fast, writing a seed or bulk load, or about to measure
latency and trust the number. This file holds the relative costs the
corpus measured and the rules for measuring. Hard bounds (transaction
size, lock timeouts) live with the method kind in
`servicer-transaction.md`; reader shapes that avoid fan-out live in
`patterns-cross-actor-reads.md`. Every number below names the project
and Reboot version it was measured at; dev-mode numbers are not
production numbers.

## Do this

### Measure in the harness, effect validation off

Production does not re-run bodies (`rbt serve` sets
`RBT_EFFECT_VALIDATION=DISABLED`; 1.6.0 source). The harness defaults
to `ENABLED`, so benchmark with it off, before and after in the same
process:

```python
import time
from reboot.aio.applications import Application
from reboot.aio.contexts import EffectValidation
from reboot.aio.tests import Reboot

rbt = Reboot()
await rbt.start()
await rbt.up(
    Application(servicers=[ShowingServicer, UserServicer]),
    effect_validation=EffectValidation.DISABLED,  # match production
)
context = rbt.create_external_context(name="bench")
samples = []
for _ in range(20):
    start = time.perf_counter()
    await User.ref("u1").add_seats(context, seat_ids=["F-12"])
    samples.append((time.perf_counter() - start) * 1000)
samples.sort()
print(f"p50 {samples[10]:.0f} ms")
```

`EffectValidation` has three values, `ENABLED`, `QUIET`, `DISABLED`
(1.6.0 `reboot/aio/contexts.py`). `rbt dev run --effect-validation`
takes `enabled|quiet|disabled` and defaults to `quiet`. `QUIET` only
rate-limits the log line; bodies still re-run, so it costs the same as
`enabled`. Run seeds and bulk loads with it disabled too: a naive
seed of about 3,600 transactions spent nearly five minutes on 193
four-hop admits with validation on (student-sor-04, 1.5.0).

### Before trusting a browser number

1. Check ambient load (`uptime`). A Spotlight reindex at load 10+ moved
   one click between 110 and 1,050 ms with no code change
   (theater-chain-20, 1.4.1).
2. Restart `rbt dev run`, then reload every open tab. A long `--watch`
   session measured p50 970 ms against 848 ms freshly restarted, about
   14% (theater-chain-20, 1.4.1, one trial per condition).
3. On macOS arm64, wait out the post-restart window: every reactive
   reader can hang and fail with `Unavailable: ping timeout` for about
   600 s after a restart (reboot-crm-07, 1.6.0; Envoy, see the `run`
   skill).
4. Take 20 samples per phase, not one.
5. Measure progress from actor state (`rbt inspect`), never from
   counting `Re-running ... to validate effects` log lines: they are
   silenced for 5 minutes per method after the first (1.6.0 source;
   client-portal-06).

### A load driver drains, it never cancels

Set a stop flag, wait for in-flight calls, cancel only overruns. A
transaction whose caller vanished held its exclusive lock until the
application restarted (reboot-air-141-load-02, 1.4.1).

## Never

- Benchmark with effect validation on and call it the app's latency —
  it re-runs every writer and transaction body (see Scales as).
- Put a cross-actor `Transaction` on a click that must feel instant —
  make it a single-actor `Writer` that schedules the follow-up
  (reboot-air-150-09: click-to-confirm 480 ms to about 60 ms, 1.5.0).
- Read an actor and then write it as two calls — have the writer
  return what the caller needs; one call is about 10x cheaper than two
  under contention (theater-chain-17).
- Wrap "do this to N things" in one transaction when N is more than a
  handful — iterate in a `Workflow`, one small transaction or writer
  per item (cineloop-40: Reset All over 48 showings stalled the suite,
  1.4.1).
- `schedule()` onto N foreign actors from one transaction — each
  becomes a two-phase-commit participant; colliding prepares killed
  the dev database worker (`database.cc:1374` assert;
  theater-network-20, 1.4.0). Capture the list into a workflow's
  request and write each actor from the workflow.
- Issue about 200 writer calls from one transaction behind a UI
  button — subscribers see nothing until the whole commit lands, which
  reads as a hang; chunk into batches (25 worked; showtime-40, 1.4.1).
- Run a background loop as a transaction holding a hot actor — a
  user's writer waits behind it; bound per-tick work (showtime-42,
  1.4.1).
- Restart only the app process (SIGTERM, let the watcher respawn) before
  measuring — afterwards every RPC measured about 50x slower for 15
  minutes (`Flight.details` 1 ms to 50 ms; reboot-air-141-load-03,
  1.4.1, undiagnosed). Restart the whole `rbt dev run`.

## Limits

- A reader that fans out to about 150 actors did not complete inside
  the request window, reactive or one-shot (`Unavailable: ping timeout`;
  theater-network-06 and -08, 1.4.0).
- Each harness test boots a runtime: about 2 s per test with nothing
  seeded (cineloop-43, 1.4.1).

## Scales as

Method kinds, harness, in-process, one call at a time, medians,
effect validation on / off (reboot-air-150-09, 1.5.0):

| Call | Kind | On | Off |
| --- | --- | --- | --- |
| `Flight.get` (288 seats) | Reader | 56 ms | 48 ms |
| `User.cart` | Reader | 32 ms | 32 ms |
| `Flight.hold` | Writer | 59 ms | 51 ms |
| `User.add_to_cart` (2 actors) | Transaction | 543 ms | 355 ms |

A transaction is roughly 5-10x a writer.

- **An actor is a lock.** Writers on one actor serialize. 40 concurrent
  holds on one seat: 75.7 s with a read-then-write pair, 7.9 s after
  the writer returned the data instead (theater-chain-17, 1.4.1);
  uncontended floor about 144 ms per hold, p50, validation off.
- **Transactions cost per participant, not per call.** 8x fewer calls
  into the same participants bought 16% (theater-chain-18, 1.4.1).
  About 10 sequential participants took about 10 s in the dev harness,
  about 4 took 2-3 s; `asyncio.gather` does not lower the
  per-participant floor (reboot-bluesky-04, 1.4.1). A four-hop
  transaction took about 1.5 s in `rbt dev run` (student-sor-04, 1.5.0).
- **Dev durable writes are flat and global**: about 150-200 ms each,
  about 5.5-6.5 constructor-writes/s however arranged (sequential,
  gathered, three concurrent chains; theater-network-13, measured
  1.3.0). Parallelism buys interleaving, not wall-clock.
- **Workflow beats a transaction chain for N creations**: 216 seats,
  54 s as a transaction chain, 15.7 s as a workflow of writer calls.
  Waves of about 20 concurrent calls were the sweet spot; about 54
  pinged out and retry-looped to 103 s (theater-network-14, 1.4.0).
- **Effect validation roughly doubles mutation latency**: 10.6 s to
  5.7 s median (reboot-bluesky-03, 1.4.1); 1.9 s to 1.4 s in the browser
  (team-memo-0826-11, 1.4.1). Nested fan-out readers pay it at every
  level: a two-level fan-out over about 100 accounts took over two
  minutes to first push; one level took about 3 s (reboot-crm-31,
  1.6.0).
- **`forall` fan-out**: 47 actors, about 2.9 s to first push, about
  twice that with validation on; later pushes are incremental
  (reboot-crm-32, 1.6.0). Over a few hundred actors it dominated the
  slow path (reboot-air-141-load-04, 1.4.1).
- **Subscriptions per page**: 50 concurrent subscriptions, slowest about
  6.8 s; one hydrated-page reader painted in about 1.5 s
  (reboot-bluesky-11, 1.4.1). 60 streams filled in about 15 s, 12 in
  about 8 s; past about 15 per page is a smell (cineloop-28, 1.4.1).
  48 subscriptions filled in progressively over about 10 s, so give
  each component its own loading state, not one page spinner
  (theater-chain-11, 1.4.1).
- **Every write persists the whole actor.** One integer of progress on
  an actor holding 8,878 records re-serializes all of them. Throughput
  did not change (11-13 items/min either way); the cost is load on the
  state store (client-portal-07, 1.6.0). Keep fast-changing fields off
  actors with big collections.
- **Key design is query cost**: an `OrderedMap` query that drops a key
  prefix was about 100x slower than one that uses it
  (reboot-air-141-load-04, 1.4.1).
- **Read-only baseline**, local dev, 4-6 users: 172.7 rps total, p50
  1-63 ms by call; with about 10% book-and-cancel writes, 8 users:
  150.6 rps, write p50 141 ms, p99 303 ms (reboot-air-141-load-04,
  1.4.1).

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `Unavailable: ping timeout` | Reader did not finish in the request window (fan-out of about 150 actors), or the post-restart Envoy window on macOS arm64 | Materialize on write; or wait out the window, see `run` |
| `Timed out waiting 30.0s to acquire exclusive lock; retry the transaction.` | A writer queued behind a long holder, possibly a vanished caller | Bound holder work; drain drivers; restart clears an orphaned lock |
| `Cannot upgrade shared lock to exclusive` | A transaction read an actor, then scheduled on it, while another chain held it | Give parallel chains their own actors; don't read before scheduling |
| `Not expecting stream to ever be done` | Browser tab outlived a backend restart | Reload the tab |

## See also

- [`patterns-cross-actor-reads.md`](patterns-cross-actor-reads.md) — reader shapes that avoid fan-out
- [`servicer-transaction.md`](servicer-transaction.md) — hard transaction limits live there
- [`testing-harness.md`](testing-harness.md) — harness setup for benchmarks
