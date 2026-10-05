---
title: Waiting in a Workflow with until and until_changes
impact: CRITICAL
impactDescription: until resolves on any non-bool return, so a None or 0 "not yet" sentinel skips the wait and ships the bug; an external poll inside until hangs forever
tags: workflow, until, until_changes, reactive, wait, approval, claim, atomic, external status, sentinel
summary: "`until` resolves on any non-`bool` return, so a `None` or `0` \"not yet\" skips the wait: return `False`. `until_changes` reacts to each change; never poll externals inside `until`."
step: servicer
applies: [mcp-ui, web-app, backend-only]
always: false
when: "you declared a `Workflow`"
via: servicer-workflow.md
verified: 1.6.0
docs: ""
---

# Waiting in a Workflow with `until` and `until_changes`

## When you are here

The workflow must block until Reboot state is true (an approval, a flag,
a free slot) or react to every change of a value. `until` /
`until_changes` suspend and re-run `callable` only when Reboot state
it read may have changed; no polling interval. They see **only Reboot
state** (a declared `Reader` on another actor, this actor's no-arg
`Service.ref().read(context)`, a stdlib actor); for external systems see
"Waiting on external work".

## Do this

### `until`: return `False` to keep waiting

`until(alias, context, callable)` waits **only while the callable
returns the bool `False`**. `True` resolves with `True`; **any non-bool
resolves immediately with that value**, whatever its truthiness
(`None`, `0`, `0.0`, `""` included;
`contexts.py::retry_reactively_until` at 1.6.0).

```python
from reboot.aio.workflows import until


@classmethod
async def control_loop(cls, context: WorkflowContext, request):
    # `get` is a declared `Reader`; inside `until` it is tracked reactively.
    async def is_approved() -> bool:
        response = await Order.ref(request.order_id).get(context)
        return response.approved

    await until("Order approval", context, is_approved)

    # To wait for a value: return False until ready; annotate the union.
    async def get_settled() -> bool | Order.GetResponse:
        response = await Order.ref(request.order_id).get(context)
        return response if response.settled else False

    settled_order = await until("Settlement", context, get_settled)
```

`until` resolves once and memoizes; replays get the memo. To wait on a
fresh condition use a new alias. With `ALWAYS` scope
(`("alias", ALWAYS)`) nothing is cached and a condition flipping back is observed.

### Atomic wait-and-update

A read in `until` then a separate write leaves a gap where another
caller takes the slot. Check **and** mutate in one inline writer and
wait on its return:

```python
class WorkerServicer(Worker.Servicer):

    @classmethod
    async def claim_slot(
        cls, context: WorkflowContext, request: ClaimRequest,
    ) -> None:
        async def try_claim(state) -> bool:
            if state.ready and not state.claimed:
                state.claimed = True
                return True  # resolves `until`
            return False

        await until(
            "Claim slot",
            context,
            lambda: Worker.ref().write(context, try_claim),
        )
```

Inline `write` is only on the workflow's own actor; for **another**
actor, declare a `Writer` there that checks, mutates and returns the
decision, and `until` on it.

### `until_changes`: react every time a value moves

Inside `context.loop`, returns when the callable's result differs from
the previous iteration's (the first iteration returns immediately).

```python
from reboot.aio.workflows import until_changes


@classmethod
async def control_loop(cls, context: WorkflowContext, request):
    async def order_status() -> str:
        response = await Order.ref(request.order_id).get(context)
        return response.status

    async for iteration in context.loop("Watch order"):
        new_status = await until_changes(
            "Order status", context, order_status,
        )
```

Equality is `==`; pass `equals=lambda prev, curr: …` where `==` is
wrong. `until` = "don't proceed until X"; `until_changes` = "act on
every change of X".

### Waiting on external work

Mirror the external status into Reboot state and `until` on it: the
external system calls a `Writer`/`Transaction` (webhook), or a loop
polls with `at_least_once` and records the result:

```python
async for iteration in context.loop("Poll job"):
    async def fetch_status() -> str:
        response = await http_client.get(f"/jobs/{job_id}")
        return response.json()["status"]

    status = await at_least_once("Job status", context, fetch_status)

    async def record(state):
        state.job_status = status
    await JobTracker.ref().per_iteration("Record status").write(context, record)

    if status == "done":
        break

# Elsewhere (e.g. a parallel workflow):
async def is_done() -> bool:
    state = await JobTracker.ref().read(context)
    return state.job_status == "done"

await until("Job done", context, is_done)
```

## Never

- `return response if ready else None` (or `0`, `0.0`, `""`) as the
  "not yet" value — a non-bool resolves at once; return `False`. One app
  refunded $0.00 without manager approval; another got `""` as a queue
  id.
- An HTTP call, SDK status check or file read inside the callable — the
  runtime can't see it change, so the wait hangs forever (or busy-polls).
- `while True: … await asyncio.sleep(5)` to poll state — not durable;
  use `until`.
- Changing an `until` callable's return type while instances are
  running — the memo holds the old type and every retry fails. Change
  the alias with the type.
- A callable that calls the same mutating method (e.g. a queue's
  `try_dequeue`) every time it re-runs — the second call on the same
  context is refused. Call it only when it will take something; return
  what it took.
- A bare `def` inline-writer callback — it must be `async def`.

## Limits

- Inside an `until` callable, bare `Service.ref().read(context)` and
  reader calls run as `always()`, so each re-run sees fresh state.
- Effect validation does not re-run `until` / `until_changes` callables.
- `until_changes` with a `bool` callable never observes a change **to**
  `False` (`False` means "keep waiting"); return a string or enum to
  watch a flag.
- An unannotated callable is assumed to return `bool`.

## Scales as

- Not measured.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `InvalidStateRefError: the 'state_id' option must be at least 1 character(s) long` | An `until` returned `""` and resolved; the empty id was used as a ref | Return `False` while waiting |
| `TypeError: Stored result of type` | Callable's return type changed after this alias memoized a value | New alias (or expunge) |
| `more than once using the same context an idempotency alias or key must be specified` | A re-run callable repeated a mutating call | Call it only when it will succeed |
| `Waiting for changes must be done _within_ a control loop` | `until_changes` outside `context.loop` | Move it inside the loop |

## See also

- [`servicer-workflow-loop.md`](servicer-workflow-loop.md) — the loop `until_changes` needs
- [`servicer-workflow-calls.md`](servicer-workflow-calls.md) — inline write rules
- [`servicer-workflow-external.md`](servicer-workflow-external.md) — polling external status
