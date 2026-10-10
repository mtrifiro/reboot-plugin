---
title: Schedule Future Work with `ref.schedule(when=...)`
impact: HIGH
impactDescription: Deferred work in asyncio timers vanishes on restart; scheduling from the wrong context fails, and bunched schedules on one actor can crash the dev database worker
tags: scheduling, schedule, spawn, timedelta, datetime, deferred, async, task, TransactionContext
summary: "asyncio timers are lost on restart and bunched schedules crash the dev database; `ref.schedule(when=...).method(context)`; which contexts schedule."
step: servicer
applies: [mcp-ui, web-app, backend-only]
always: false
when: "deferring work with `schedule()` or `spawn(when=…)`"
verified: 1.6.0
docs: ""
---

# Schedule Future Work with `ref.schedule(when=...)`

## When you are here

A method needs a call to happen later (expiry, reminder, next tick) or
right after it commits (kicking off a workflow). The schedule persists
with the surrounding writer/transaction, so it survives restarts.
Recurring / "cron" jobs: [`scheduling-recurring.md`](scheduling-recurring.md).

## Do this

From a writer, schedule a method on the actor itself (as in the
[`reboot-bank-pydantic`](https://github.com/reboot-dev/reboot-bank-pydantic)
example, `backend/src/main.py`). API `api/bank/v1/account.py` declares
`open=Writer(request=OpenRequest, response=None, factory=True, …)` and
`interest=Writer(request=None, response=None, …)`; `main.py`:

```python
from datetime import datetime, timedelta, timezone


class AccountServicer(Account.Servicer):

    async def open(
        self, context: WriterContext, request: Account.OpenRequest,
    ) -> None:
        await self.ref().schedule(when=timedelta(seconds=1)).interest(context)
        # Or at an instant (timezone-aware):
        # await self.ref().schedule(
        #     when=datetime(2030, 1, 1, 2, 0, tzinfo=timezone.utc),
        # ).interest(context)
```

`when=` is a `timedelta` (delay) or a **timezone-aware `datetime`**
(instant); omitted, it fires when the surrounding method commits. It
fires at or after the requested time; past-due schedules fire as soon
as the app is back up.

Schedulable refs by context (generated client, 1.6.0):

| Context | Form | Targets |
| --- | --- | --- |
| Writer | `self.ref().schedule(when=…).m(context)` | own actor only |
| Transaction | `Account.ref(other_id).schedule(when=…).m(context)` | any actor |
| Workflow | `Account.ref(other_id).spawn(when=…).m(context)` | any actor |
| `ExternalContext` | `Account.ref(id).spawn(when=…).m(context)` | any actor |

To reach another actor from a writer, schedule a method on `self` that
calls it; make that method a workflow so no transaction lock is held
while it runs.

## Never

- `asyncio.create_task(...)` / `asyncio.sleep(...)` for delayed work —
  lost on restart, not transactional.
- `Account.ref(other_id).schedule(...)` from a **writer** — overloads for
  another actor accept only `TransactionContext` (mypy reports an opaque
  overload mismatch). Schedule on `self`, or make the method a
  transaction (Writer → Transaction is schema-compatible).
- `….schedule(when=…)` from a **workflow**, on any ref — raises
  `TypeError` every attempt and retries forever; mypy misses it. Use
  `spawn(when=…)` ([`servicer-workflow-declare.md`](servicer-workflow-declare.md)).
- Several scheduled transactions on one actor with the same `when=` (one
  `expire_hold` per seat) — their two-phase-commit prepares collide and
  a native assert kills the worker (observed at 1.4.0). Schedule one
  task per logical event covering all the work.
- A transaction that loops `schedule()` onto N foreign actors — it
  crashed the database worker within minutes under contention; fan out
  from a workflow (`servicer-transaction.md` § Never).
- A naive `datetime` — interpreted in the server's local zone.
- Relying on a reader that computes "expired" at read time to update
  other viewers — reactive readers push mutations, not derived values.
  Commit the transition with a scheduled writer; keep the read-time
  check as source of truth in case the schedule fires late.

## Limits

- Constructors cannot be scheduled or spawned.
- No delivery order between scheduled tasks: stamp each note with a
  per-entity generation and drop notes below the high-water mark
  (observed at 1.4.0).
- A scheduled method raising `<Method>Aborted` has that as its result;
  it is not retried.
- Retry backoff can re-synchronize tasks scheduled apart, and a restart
  fires every past-due timer at once; a timer backlog on one actor
  became a crash loop only `rbt dev expunge` cleared (observed at 1.4.0,
  framework issue). Keep an actor's timers few and coarse; never hold a
  lock across a cross-actor round-trip.
- An undeclared exception in a scheduled method is retried with backoff; a declared `<Method>Aborted` is not (marquee-control, 1.4.1).

## Scales as

- `schedule()` writes the target's task queue: a transaction that read
  the actor then schedules on it upgrades its shared lock to exclusive,
  so concurrent chains on one actor collide; give parallel chains their
  own actors (observed at 1.3.0).
- Dev-mode durable writes cost about 150–200 ms each, globally: about
  5.5–6.5 constructor-writes/second however arranged (measured at
  1.3.0). Make partial progress usable instead of chasing total time.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `TypeError: reboot.aio.contexts.WorkflowContext is not an instance or subclass of one of the expected type(s): ['reboot.aio.contexts.TransactionContext']` | `schedule()` from a workflow | `spawn(when=…)` |
| `Cannot upgrade shared lock to exclusive` | Concurrent transactions read, then schedule on, the same actor | Give parallel chains their own actors; don't read before scheduling |
| `database.cc:1374] Check failed: inserted` | Simultaneous scheduled transactions on one actor, or a restart firing every past-due timer at once (worker exits with status -6) | One task per event; timer methods that only schedule per-actor work; expunge dev state if it crash-loops |

## See also

- [`scheduling-recurring.md`](scheduling-recurring.md) — recurring and cron jobs
- [`servicer-workflow-declare.md`](servicer-workflow-declare.md) — starting workflows, spawn
- [`servicer-transaction.md`](servicer-transaction.md) — transaction participant cost
