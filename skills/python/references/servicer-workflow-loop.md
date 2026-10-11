---
title: Iterating in a Workflow with context.loop
impact: HIGH
impactDescription: A while-loop replays every iteration from the start; a renamed or second loop breaks progress tracking or raises
tags: workflow, loop, context.loop, iteration, interval, control loop, checkpoint, per_iteration
summary: "`while` replays every iteration; use `context.loop(\"Name\")`, never renamed or doubled; per-iteration call scope; `interval=` pacing."
step: servicer
applies: [mcp-ui, web-app, backend-only]
always: false
when: "you declared a `Workflow`"
via: servicer-workflow.md
verified: 1.6.0
docs: ""
---

# Iterating in a Workflow with `context.loop`

## When you are here

The workflow repeats a body: a queue consumer, a control loop, a poller,
a pass over N items each needing a checkpoint. `context.loop(alias)` is
an async iterator that checkpoints every iteration, so a restart resumes
at the current one. Call scoping:
[`servicer-workflow-calls.md`](servicer-workflow-calls.md); reacting to
a changed value: `until_changes` in
[`servicer-workflow-wait.md`](servicer-workflow-wait.md).

## Do this

```python
@classmethod
async def control_loop(
    cls,
    context: WorkflowContext,
    request: ControlLoopRequest,
):
    topic = Topic.ref(f"{request.channel_id}-messages")
    queue = Queue.ref(f"{context.state_id}-messages-queue")

    # Setup: re-runs as Python on replay, but per_workflow-scoped by default.
    await topic.subscribe(context, queue_id=queue.state_id)

    async for iteration in context.loop("Control loop"):
        # per_iteration-scoped by default.
        dequeue = await queue.dequeue(context, bulk=True)
        message_ids = [as_str(item.value) for item in dequeue.items]
        # ... process this iteration's batch ...
```

- The counter persists when an iteration completes; a restart resumes at
  the incomplete one.
- Reboot calls before the loop default to `per_workflow` (one-shot setup
  like `subscribe` takes effect once); inside, `per_iteration`.
- `iteration` is the index from 0, replay-stable, safe in aliases
  (`f"Process batch {iteration}"`).
- `break` / `return` ends the loop; the workflow continues after the
  `async for` or completes.
- Pacing: `context.loop("Poll", interval=timedelta(seconds=30))` waits
  `interval` after each completed iteration.

## Never

- `while True:` in a workflow — no iteration boundary, so replay re-runs
  every iteration from the start.
- Renaming the loop alias after work has started — it is the replay
  correlation key; renaming invalidates progress tracking.
- A second `context.loop(...)` in the same workflow, sequential or
  nested — raises. Split into two workflows.
- `await asyncio.sleep(n)` between iterations for pacing — use
  `interval=`.
- A `break` decision derived from a non-memoized external read or the
  clock — the last iteration re-runs (see Limits) and must break again.
  Base it on memoized values or Reboot state.

## Limits

- One loop per workflow (1.6.0 runtime).
- The **final** iteration's completion is never recorded: after a
  restart, and under dev-mode effect validation, it runs again (memoized
  steps return cached results) and must reach the same `break`/`return`.
- Setup that is not a scoped Reboot call or memoized primitive (a print,
  a plain external call) runs on every replay.

## Scales as

- A `context.loop` workflow issuing plain writer calls replaced a
  self-scheduling tick transaction that serialized everything and capped
  a load simulator at about 1 op/s (observed at 1.4.0).

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `Only one loop per workflow is currently supported` | A second `context.loop` in the same workflow | One loop per workflow; split into two workflows |
| `While validating effects, the re-run of the last iteration of the` | The re-run last iteration did not break | Make the break condition replay-stable |

## See also

- [`servicer-workflow-wait.md`](servicer-workflow-wait.md) — `until_changes` per iteration
- [`stdlib-queue.md`](stdlib-queue.md) — the queue a consumer loop drains
- [`scheduling-recurring.md`](scheduling-recurring.md) — wall-clock recurring jobs
