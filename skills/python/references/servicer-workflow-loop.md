---
title: Iterating in a Workflow with context.loop
impact: HIGH
impactDescription: A while-loop replays every iteration from the start; a renamed or second loop breaks progress tracking or raises
tags: workflow, loop, context.loop, iteration, interval, control loop, checkpoint, per_iteration
summary: "Iterate with `context.loop(\"Name\")`, never `while`, which replays every iteration; calls default to per-iteration scope; never rename a loop or add a second; `interval=` paces it."
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

Your workflow should repeat a body: a consumer that drains a queue, a
control loop that reacts to messages, a poller, a pass over N items
that each need their own checkpoint. `context.loop(alias)` is an async
iterator that checkpoints every iteration, so a restart resumes at the
current iteration instead of the first. Scoping the calls inside the
loop is in [`servicer-workflow-calls.md`](servicer-workflow-calls.md);
reacting to a changed value per iteration is `until_changes` in
[`servicer-workflow-wait.md`](servicer-workflow-wait.md).

## Do this

```python
@classmethod
async def control_loop(
    cls,
    context: WorkflowContext,
    request: ControlLoopRequest,
):
    channel = Channel.ref(request.channel_id)
    pub_sub = PubSub.ref(f"{request.channel_id}-pub-sub")
    queue = Queue.ref(f"{context.state_id}-messages-queue")

    await pub_sub.subscribe(
        context, topic="messages", queue_id=queue.state_id,
    )

    async for iteration in context.loop("Control loop"):
        dequeue = await queue.dequeue(context, bulk=True)

        message_ids = [as_str(item.value) for item in dequeue.items]
        # ... process this iteration's batch ...
```

- **Each iteration is a checkpoint.** The iteration counter is persisted
  when an iteration completes; after a restart the workflow resumes at
  the iteration that had not completed.
- **Setup before the loop** re-executes as Python on every replay, but
  its Reboot calls default to `per_workflow` scope and return their
  memoized results, so one-shot setup such as the `subscribe` above
  takes effect once.
- **Calls inside the loop** default to `per_iteration` scope: each
  iteration is a fresh memo scope, replay-safe within the iteration.
- **`iteration`** is the iteration index (from 0). It is replay-stable,
  so it is safe inside aliases (`f"Process batch {iteration}"`).
- **`break` or `return`** ends the loop; the workflow then continues
  after the `async for` or completes.
- **Pacing:** `context.loop("Poll", interval=timedelta(seconds=30))`
  waits `interval` after each completed iteration before starting the
  next.

## Never

- `while True:` in a workflow — there is no iteration boundary, so
  replay re-runs every iteration from the start.
- Renaming the loop alias after work has started — it is the replay
  correlation key; renaming invalidates progress tracking.
- A second `context.loop(...)` in the same workflow, sequential or
  nested — raises. Split the work into two workflows.
- `await asyncio.sleep(n)` between iterations for pacing — use
  `interval=`.
- A `break` decision derived from a non-memoized external read or the
  clock — the last iteration is re-run (see Limits) and must break
  again. Base the decision on memoized values or Reboot state.

## Limits

- One loop per workflow (1.6.0 runtime).
- The **final** iteration's completion is never recorded: after a
  restart, and under dev-mode effect validation, the last iteration
  runs again. Its memoized steps return cached results, and it must
  reach the same `break`/`return`.
- Setup code that is not a scoped Reboot call or a memoized primitive
  (a print, a plain external call) runs again on every replay.

## Scales as

- A `context.loop` workflow issuing plain writer calls replaced a
  self-scheduling tick transaction that serialized every operation and
  capped a load simulator at about 1 op/s (observed at 1.4.0).

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `Only one loop per workflow is currently supported` | A second `context.loop` in the same workflow | One loop per workflow; split into two workflows |
| `While validating effects, the re-run of the last iteration of the` | The re-run last iteration did not break | Make the break condition replay-stable |
| `Waiting for changes must be done _within_ a control loop` | `until_changes` called outside `context.loop` | Move it inside the loop |

## See also

- [`servicer-workflow-wait.md`](servicer-workflow-wait.md) — `until_changes` per iteration
- [`stdlib-queue.md`](stdlib-queue.md) — the queue a consumer loop drains
- [`scheduling-recurring.md`](scheduling-recurring.md) — wall-clock recurring jobs
