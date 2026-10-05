---
title: Schedule Future Work with `ref.schedule(when=...)`
impact: HIGH
impactDescription: Deferred work in asyncio timers vanishes on restart; scheduling from the wrong context fails, and bunched schedules on one actor can crash the dev database worker
tags: scheduling, schedule, spawn, timedelta, datetime, deferred, async, task, TransactionContext
summary: "Durable deferred work with `ref.schedule(when=...).method(context)`, never asyncio timers; which contexts may schedule; bunched schedules on one actor can crash the dev database worker."
step: servicer
applies: [mcp-ui, web-app, backend-only]
always: false
when: "deferring work with `schedule()` or `spawn(when=…)`"
verified: 1.6.0
docs: ""
---

# Schedule Future Work with `ref.schedule(when=...)`

## When you are here

A method needs another call to happen later (an expiry, a reminder, the
next tick) or right after it commits (kicking off a workflow). Reboot
persists the schedule with the surrounding writer/transaction, so it
survives restarts. Recurring and "cron" jobs are in
[`scheduling-recurring.md`](scheduling-recurring.md).

## Do this

From a writer, schedule a method on the actor itself (matches the
[`reboot-bank-pydantic`](https://github.com/reboot-dev/reboot-bank-pydantic)
example, `backend/src/main.py`):

`api/bank/v1/account.py`:

```python
open=Writer(
    request=OpenRequest, response=None, factory=True,
    description="Bring the account into existence with a zero balance.",
    mcp=None,
),
interest=Writer(
    request=None, response=None,
    description="Credit one period's interest at the current rate.",
    mcp=None,
),
```

`main.py`:

```python
from datetime import timedelta


class AccountServicer(Account.Servicer):

    async def open(
        self, context: WriterContext, request: Account.OpenRequest,
    ) -> None:
        await self.ref().schedule(when=timedelta(seconds=1)).interest(context)
```

`when=` takes a `timedelta` (fire after that delay) or a
**timezone-aware `datetime`** (fire at that instant); omit it to fire as
soon as the surrounding method commits. The call fires at or after the
requested time; a past-due schedule fires immediately when the app comes
back up.

```python
from datetime import datetime, timezone

await self.ref().schedule(
    when=datetime(2030, 1, 1, 2, 0, tzinfo=timezone.utc),
).interest(context)
```

Which ref you may schedule on depends on your context (generated client,
1.6.0):

| Context | Form | Targets |
| --- | --- | --- |
| Writer | `self.ref().schedule(when=…).m(context)` | own actor only |
| Transaction | `Account.ref(other_id).schedule(when=…).m(context)` | any actor |
| Workflow | `Account.ref(other_id).spawn(when=…).m(context)` | any actor |
| `ExternalContext` | `Account.ref(id).spawn(when=…).m(context)` | any actor |

To reach another actor from a writer, schedule a method on `self` that
then calls it; making that method a workflow avoids holding a
transaction's lock while it runs.

## Never

- `asyncio.create_task(...)` / `asyncio.sleep(...)` for delayed work —
  disappears on restart and is not transactional.
- `Account.ref(other_id).schedule(...)` from a **writer** — the generated
  overloads for another actor accept only `TransactionContext`, and mypy
  reports an opaque overload mismatch. Schedule on `self`, or make the
  method a transaction (Writer → Transaction is schema-compatible).
- `….schedule(when=…)` from a **workflow**, on any ref — raises
  `TypeError` on every attempt and the task retries forever; mypy does
  not catch it. Use `spawn(when=…)`, same `when=`
  ([`servicer-workflow-declare.md`](servicer-workflow-declare.md)).
- Several scheduled transactions on one actor with the same `when=` (one
  `expire_hold` per seat) — they fire together, their two-phase-commit
  prepares collide, and a native assert kills the worker (observed at
  1.4.0). Schedule one task per logical event that covers all the work.
- A transaction that loops `schedule()` onto N foreign actors — every
  target joins one N-party two-phase commit; it crashed the database
  worker within minutes under contention (observed at 1.4.0). Pass the
  list to a workflow and fan out from there.
- A naive `datetime` — it is interpreted in the server's local zone.
- Relying on a reader that computes "expired" at read time to update
  other viewers — reactive readers push mutations, not derived values.
  Commit the transition with a scheduled writer; keep the read-time
  check as the source of truth if the schedule fires late.

## Limits

- Constructors cannot be scheduled or spawned.
- No delivery-order guarantee between scheduled tasks: two notes about
  the same entity can land in either order. Stamp each with a
  per-entity generation and drop notes below the high-water mark
  (observed at 1.4.0).
- If the scheduled method raises a `<Method>Aborted`, that is its result;
  the invocation is not retried.
- Retry backoff can re-synchronize tasks scheduled apart, and a restart
  fires every past-due timer at once; a backlog of timers on one actor
  became a crash loop that only `rbt dev expunge` cleared (observed at
  1.4.0, framework issue). Keep an actor's timers few and coarse, and
  never hold a lock across a cross-actor round-trip.

## Scales as

- `schedule()` is a write to the target's task queue. A transaction that
  has read the actor and then schedules on it upgrades its shared lock to
  exclusive, so concurrent chains on one actor collide; give parallel
  chains their own actors (observed at 1.3.0).
- Dev-mode durable writes cost about 150–200 ms each, globally: about
  5.5–6.5 constructor-writes/second however the work is arranged
  (measured at 1.3.0). Make partial progress usable instead of chasing
  total time.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `TypeError: reboot.aio.contexts.WorkflowContext is not an instance or subclass of one of the expected type(s): ['reboot.aio.contexts.TransactionContext']` | `schedule()` from a workflow | `spawn(when=…)` |
| `Cannot upgrade shared lock to exclusive` | Concurrent transactions read then schedule on the same actor | Separate actors per chain |
| `database.cc:1374] Check failed: inserted` | Simultaneous scheduled transactions on one actor (worker exits with status -6) | One task per event; expunge dev state if it crash-loops |

## See also

- [`scheduling-recurring.md`](scheduling-recurring.md) — recurring and cron jobs
- [`servicer-workflow-declare.md`](servicer-workflow-declare.md) — starting workflows, spawn
- [`servicer-transaction.md`](servicer-transaction.md) — transaction participant cost
