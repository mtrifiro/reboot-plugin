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

Something must run every N seconds, every day at 02:00, or at the top of
each hour. Reboot has **no cron daemon**: `schedule(when=...)` fires
**once**, and a recurring job is a method that schedules its own next
firing before it returns. The persisted chain survives restarts with no
infrastructure outside the app. One-shot scheduling and which context
may schedule what are in [`scheduling-basic.md`](scheduling-basic.md).

## Do this

Three methods on **one** actor:

1. **`start()`** — a `Writer(factory=True)` that kicks off the first tick.
2. **`tick()`** — a `Writer` that schedules `run()` now, then the next
   `tick()` at the next wall-clock time.
3. **`run()`** — a `Workflow` that does one occurrence's work.

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
        # Kick off the first tick at the next 02:00 UTC.
        await self.ref().schedule(
            when=_next_2am_utc(datetime.now(timezone.utc)),
        ).tick(context)

    async def tick(self, context: WriterContext) -> None:
        # Run this occurrence now — `schedule()` with no `when=` fires
        # immediately — then line up the next tick.
        await self.ref().schedule().run(context)

        if self.state.active:
            await self.ref().schedule(
                when=_next_2am_utc(datetime.now(timezone.utc)),
            ).tick(context)

    @classmethod
    async def run(
        cls, context: WorkflowContext, request: RunRequest,
    ) -> None:
        # The durable per-occurrence work: external API calls, LLM
        # calls, multiple steps. See `servicer-workflow.md`.
        ...
```

- The re-schedule sits in the same writer as the state change, so both
  commit atomically: no window where the tick ran but the next failed to
  enqueue.
- Recompute the next **absolute** time each tick. `+timedelta(days=1)`
  from "now" drifts later every day; a `timedelta` cadence ("every ~N
  seconds") is fine when drift does not matter.
- Keeping `tick()` thin means a slow, failing or retrying `run()` never
  delays the cadence, and each `run()` checkpoints and retries on its own.
- Create the actor once (e.g. from `initialize`, idempotently) and the
  chain runs until `active` is cleared.

The simplest form, a writer that re-schedules itself (the
[`reboot-bank-pydantic`](https://github.com/reboot-dev/reboot-bank-pydantic)
example), is the same idea without `run()`:

```python
async def interest(self, context: WriterContext) -> None:
    self.state.balance += 1
    if self.state.active:
        await self.ref().schedule(
            when=timedelta(seconds=random.randint(1, 4))
        ).interest(context)


async def deactivate(self, context: WriterContext) -> None:
    self.state.active = False
```

### Variants

- **`run()` need not be a workflow.** If one occurrence is only a state
  mutation, make it a `Writer` (or a `Transaction` across actors).
- **Wait for each run to succeed.** Drop `tick()` and have `run()`
  schedule the next `run()` as its **last** step; occurrences then never
  overlap, and a failing run pauses the recurrence. From inside a
  workflow that step is `spawn(when=…)`, not `schedule(when=…)`.
- **Inside a long-lived workflow**, `context.loop("…", interval=…)` paces
  iterations ([`servicer-workflow-loop.md`](servicer-workflow-loop.md)).

## Never

- A one-shot `schedule(when=…)` expecting it to recur — it fires once.
- `….schedule(when=…)` from inside a workflow `run()` to line up the next
  occurrence — raises `TypeError` and retries forever. Use
  `spawn(when=…)` ([`scheduling-basic.md`](scheduling-basic.md)).
- A naive `datetime` in `when=` — read in the server's local zone, so
  "02:00" differs by machine. Use `datetime.now(timezone.utc)` or
  `tzinfo=timezone.utc`.
- `datetime.now()` read directly in a **workflow** body — it differs on
  every replay. Capture it with `at_least_once`
  ([`servicer-workflow-external.md`](servicer-workflow-external.md)).
- A "set active" writer that overwrites an existing generation token on a
  redundant start — the pending tick no longer owns the token and dies,
  while the caller sees "already active" and schedules nothing. Write the
  token only on the inactive → active transition.
- Starting `run()` from both the chain and another entry point (an admin
  button, a startup hook) without a claim — passes overlap
  ([`servicer-workflow-declare.md`](servicer-workflow-declare.md)).

## Limits

- **Catch-up fires once, not a backfill.** A tick due while the app was
  down fires immediately on restart, then the cadence resumes; three
  missed days give one run. To backfill, compare the clock with a
  last-run timestamp in state and act explicitly.
- **A dead chain is silent:** no task-failure warning, no log line;
  the recurring thing just stops. Suspect the guard condition first.
  The effect-validation "Re-running" log line marks executions but
  silences itself for 5 minutes (observed at 1.4.1).
- **Wall clock in a writer tick.** Reading `datetime.now(timezone.utc)`
  to compute `when=` is fine: scheduling time is not replay-validated.
  Persisting a clock or random value from a writer is fine when it is
  only **observed** (a deadline, `created_at`, a display token), because
  effect validation aborts and re-runs the body rather than comparing
  runs. It is a bug when something must later re-derive or **address**
  it (an actor id, idempotency key, foreign key, a code the user quotes
  back); derive those deterministically, or pass them in the request.
- **Stopping is a state flag or a generation token**, never a kill:
  stopping `rbt dev run` only pauses the chain. A per-key generation that
  each tick checks before acting makes stop/restart safe.

## Scales as

- A self-scheduling tick **transaction** serializes every operation in
  one transaction; a load simulator built that way capped at about
  1 op/s and was replaced by a `context.loop` workflow (observed at
  1.4.0).

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `TypeError: reboot.aio.contexts.WorkflowContext is not an instance or subclass of one of the expected type(s)` | `schedule()` called from a workflow | `spawn(when=…)` |

## See also

- [`scheduling-basic.md`](scheduling-basic.md) — `when=`, contexts, timer limits
- [`servicer-workflow-declare.md`](servicer-workflow-declare.md) — the `run()` workflow
- [`servicer-writer.md`](servicer-writer.md) — the tick writer's rules
