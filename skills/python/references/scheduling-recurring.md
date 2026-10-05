---
title: Recurring and "Cron" Schedules by Self-Rescheduling
impact: MEDIUM
impactDescription: Without a self-reschedule the recurring tick stops after one fire; reaching for an OS cron daemon loses durability; a redundant start can orphan the chain
tags: scheduling, recurring, periodic, cron, wall-clock, daily, hourly, self-reschedule, workflow, generation token
summary: "A recurring job reschedules itself (`start()` → `tick()` → `run()`), never OS cron; a dead chain is silent, catch-up fires once, stopping is a state flag or generation token."
step: servicer
applies: [mcp-ui, web-app, backend-only]
always: false
when: "the app needs a recurring or cron job"
verified: 1.6.0
docs: ""
---

# Recurring and "Cron" Schedules by Self-Rescheduling

## When you are here

Something must run every N seconds, daily at 02:00, or hourly. Reboot
has **no cron daemon**: `schedule(when=...)` fires **once**, so a
recurring job schedules its own next firing before returning; the
persisted chain survives restarts. One-shot scheduling and which context
schedules what: [`scheduling-basic.md`](scheduling-basic.md).

## Do this

Three methods on **one** actor: **`start()`** (`Writer(factory=True)`,
first tick), **`tick()`** (`Writer`: schedules `run()` now and the next
`tick()`), **`run()`** (`Workflow`: one occurrence's work).

```python
from datetime import datetime, timedelta, timezone
from reboot.aio.contexts import WorkflowContext, WriterContext


def _next_2am_utc(now: datetime) -> datetime:
    # The next 02:00 UTC strictly after `now`.
    target = now.replace(hour=2, minute=0, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return target


class NightlyReportServicer(NightlyReport.Servicer):

    async def start(
        self, context: WriterContext, request: StartRequest,
    ) -> None:
        self.state.active = True
        await self.ref().schedule(
            when=_next_2am_utc(datetime.now(timezone.utc)),
        ).tick(context)

    async def tick(self, context: WriterContext) -> None:
        await self.ref().schedule().run(context)  # no `when=`: now
        if self.state.active:
            await self.ref().schedule(
                when=_next_2am_utc(datetime.now(timezone.utc)),
            ).tick(context)

    @classmethod
    async def run(
        cls, context: WorkflowContext, request: RunRequest,
    ) -> None:
        # Durable per-occurrence work; see `servicer-workflow.md`.
        ...
```

- The re-schedule commits atomically with the writer's state change: no
  window where the tick ran but the next failed to enqueue.
- Recompute the next **absolute** time each tick; `+timedelta(days=1)`
  from "now" drifts later daily. A `timedelta` cadence ("every ~N
  seconds") is fine when drift doesn't matter.
- A thin `tick()` means a slow or retrying `run()` never delays the
  cadence; each `run()` checkpoints and retries on its own.
- Create the actor once (e.g. idempotently from `initialize`); the chain
  runs until `active` is cleared.
- Simplest form, no `run()`: a writer that re-schedules itself
  ([`reboot-bank-pydantic`](https://github.com/reboot-dev/reboot-bank-pydantic)):

```python
async def interest(self, context: WriterContext) -> None:
    self.state.balance += 1
    if self.state.active:  # `deactivate` writer sets it False
        await self.ref().schedule(
            when=timedelta(seconds=random.randint(1, 4))
        ).interest(context)
```

### Variants

- **`run()` need not be a workflow**: a pure state mutation is a
  `Writer` (or `Transaction` across actors).
- **Wait for each run to succeed**: drop `tick()`; `run()` schedules the
  next `run()` as its **last** step, so occurrences never overlap and a
  failing run pauses the recurrence. From a workflow that step is
  `spawn(when=…)`, not `schedule(when=…)`.
- **Inside a long-lived workflow**, `context.loop("…", interval=…)` paces
  iterations ([`servicer-workflow-loop.md`](servicer-workflow-loop.md)).

## Never

- A one-shot `schedule(when=…)` expecting it to recur — it fires once.
- `….schedule(when=…)` from inside a workflow `run()` to line up the next
  occurrence — raises `TypeError`, retries forever. Use `spawn(when=…)`
  ([`scheduling-basic.md`](scheduling-basic.md)).
- A naive `datetime` in `when=` — server-local zone, so "02:00" differs
  by machine. Use `datetime.now(timezone.utc)` or `tzinfo=timezone.utc`.
- `datetime.now()` read directly in a **workflow** body — differs every
  replay; capture it with `at_least_once`
  ([`servicer-workflow-external.md`](servicer-workflow-external.md)).
- A "set active" writer that overwrites an existing generation token on a
  redundant start — the pending tick loses the token and dies while the
  caller sees "already active" and schedules nothing. Write the token
  only on the inactive → active transition.
- Starting `run()` from both the chain and another entry point (an admin
  button, a startup hook) without a claim — passes overlap
  ([`servicer-workflow-declare.md`](servicer-workflow-declare.md)).

## Limits

- **Catch-up fires once, not a backfill**: a tick due during downtime
  fires on restart, then the cadence resumes (three missed days = one
  run). To backfill, compare the clock with a last-run timestamp in state.
- **A dead chain is silent**: no warning, no log line; suspect the guard
  condition first. The effect-validation "Re-running" log line marks
  executions but silences itself for 5 minutes (observed at 1.4.1).
- **Wall clock in a writer tick**: `datetime.now(timezone.utc)` for
  `when=` is fine (scheduling time is not replay-validated). Persisting a
  clock/random value from a writer is fine when only **observed** (a
  deadline, `created_at`, a display token), because effect validation
  re-runs the body rather than comparing runs. It is a bug when it must
  later be re-derived or **addressed** (actor id, idempotency key,
  foreign key, a code the user quotes back): derive those
  deterministically or pass them in the request.
- **Stopping is a state flag or a generation token**, never a kill
  (stopping `rbt dev run` only pauses the chain). A per-key generation
  each tick checks before acting makes stop/restart safe.

## Scales as

- A self-scheduling tick **transaction** serializes every operation; a
  load simulator built that way capped at about 1 op/s and was replaced
  by a `context.loop` workflow (observed at 1.4.0).

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `TypeError: reboot.aio.contexts.WorkflowContext is not an instance or subclass of one of the expected type(s)` | `schedule()` called from a workflow | `spawn(when=…)` |

## See also

- [`scheduling-basic.md`](scheduling-basic.md) — `when=`, contexts, timer limits
- [`servicer-workflow-declare.md`](servicer-workflow-declare.md) — the `run()` workflow
- [`servicer-writer.md`](servicer-writer.md) — the tick writer's rules
