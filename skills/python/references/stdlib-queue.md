---
title: Use `Queue` for Durable FIFO Work Queues
tags: stdlib, Queue, FIFO, enqueue, dequeue, try_dequeue, durable, consumer loop
summary: "Durable FIFO `Queue`: producers enqueue, a `Workflow` consumer loop dequeues, transactions try-dequeue; no `create`; start the consumer with an alias; `empty` aborts before the first enqueue."
impact: HIGH
impactDescription: Workflows pulling work from a Queue is the canonical "consumer loop" pattern
step: servicer
applies: [mcp-ui, web-app, backend-only]
always: false
when: "the design uses a work `Queue`"
verified: 1.6.0
docs: ""
---

# Use `Queue` for Durable FIFO Work Queues

## When you are here

The design needs a durable FIFO (work, job or intake queue). `Queue`
(`reboot.std.collections.queue.v1.queue`) is a durable FIFO of `Item`
values backed by an internal stdlib sorted-map actor: producers
`enqueue` from any mutating context; a workflow consumer `dequeue`s,
blocking until items arrive. Don't define your own queue type. Fan-out:
`stdlib-pubsub.md`; `Item`: `stdlib-item.md`.

## Do this

| Method | Kind | Notes |
| --- | --- | --- |
| `enqueue` | transaction | exactly one of `value` / `bytes` / `any` (single) or `items: list[Item]` (bulk) |
| `dequeue` | workflow | blocks until at least one item; `bulk: bool`, `at_most?: int` |
| `try_dequeue` | transaction | non-blocking; empty response if nothing is there |
| `empty` | reader | whether the queue holds nothing |

There is no `create`: unlike `OrderedMap`, a `Queue` builds its backing
sorted map on first use; enqueue straight onto a ref.

```python
from reboot.aio.contexts import WorkflowContext
from reboot.aio.external import InitializeContext
from reboot.std.collections.queue.v1 import queue
from reboot.std.collections.queue.v1.queue import Queue
from reboot.std.collections.v1.sorted_map import sorted_map_library
from reboot.std.item.v1.item import Item


class ProducerServicer(Producer.Servicer):

    async def submit(
        self, context: TransactionContext, request: SubmitRequest,
    ) -> SubmitResponse:
        await Queue.ref(WORK_QUEUE_ID).enqueue(context, value=request.payload)
        # Bulk: enqueue(context, items=[Item(value=p) for p in payloads])
        return SubmitResponse()


class ConsumerServicer(Consumer.Servicer):

    @classmethod
    async def control_loop(cls, context: WorkflowContext, request):
        queue = Queue.ref(f"{context.state_id}-work")
        async for iteration in context.loop("Consume"):
            response = await queue.per_iteration(
                "Dequeue work",
            ).dequeue(context, bulk=True)
            for item in response.items:
                ...  # item.value / item.bytes / item.any, as enqueued


async def initialize(context: InitializeContext):
    await Consumer.ref(CONSUMER_ID).idempotently(
        "Start consumer",
    ).spawn().control_loop(context)


async def main():
    await Application(
        servicers=[ProducerServicer, ConsumerServicer] + queue.servicers(),
        libraries=[sorted_map_library()],
        initialize=initialize,
    ).run()
```

- `queue.servicers()` is `[QueueServicer] + sorted_map.servicers()`;
  `Application` deduplicates, so also listing `sorted_map_library()` is
  harmless. For an authorizer, register
  `libraries=[queue_library(authorizer=...), sorted_map_library()]`
  (`queue_library` from the same module; requires the sorted-map
  library). Never use the sorted-map types in app code; a user-facing
  sorted collection is `OrderedMap` (`stdlib-ordered-map.md`).
- `dequeue` blocks until an item arrives (no polling). `bulk=True`
  returns up to `DEFAULT_BULK_COUNT` (64); `at_most=N` caps the batch.
- The `"Start consumer"` alias is required in `initialize` and stops
  each boot starting another consumer. From a transaction use
  `Consumer.ref(id).schedule().control_loop(context)`
  (`servicer-workflow-declare.md`).
- From a transaction,
  `Queue.ref(WORK_QUEUE_ID).try_dequeue(context, bulk=True, at_most=10)`
  returns the same shape, with no items instead of blocking.

## Never

- `Queue.ref(id).create(context)` — no constructor
  (`'WeakReference' object has no attribute 'create'`); enqueue directly.
- `dequeue` from a writer or transaction — workflow-only; use
  `try_dequeue` there.
- A bare `.spawn()` of the consumer from `initialize` — raises
  `IdempotencyRequiredError`; use `.idempotently("alias").spawn()`.
- Reading `empty` on a queue that may never have been enqueued to —
  aborts `StateNotConstructed` (observed at 1.6.0); a workflow retries
  forever. Use `try_dequeue` (empty on an unused queue), a blocking
  `dequeue`, or enqueue once first.
- Calling `try_dequeue` twice on the same queue from one `until`
  callable — the second is refused without an alias
  (`servicer-workflow-wait.md`).
- Hand-rolling a queue as a list field on actor state.

## Limits

- `QueueServicer`'s default authorizer is
  `allow_if(all=[is_app_internal])`: only your servicers can
  enqueue/dequeue; browsers and MCP clients go through your methods or
  `queue_library(authorizer=...)`.
- `enqueue` takes exactly one of `value`, `bytes`, `any`, `items`;
  anything else raises `TypeError` (`stdlib-item.md`).
- A bulk `dequeue`/`try_dequeue` without `at_most` takes at most 64.
- FIFO order is by a UUIDv7 key assigned at enqueue time.

## Scales as

- Not measured. An idle `dequeue` parks in `until` and costs nothing
  while the queue is empty (reboot-crm, 1.6.0). Each `enqueue` is one
  transaction on the queue plus an insert into its sorted map.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `'WeakReference' object has no attribute 'create'` | Tried to construct a `Queue` | Enqueue directly |
| `IdempotencyRequiredError: Calls to mutators from within your initialize function must use idempotency` | Bare `.spawn()` of the consumer in `initialize` | `.idempotently("Start consumer").spawn()` |
| `StateNotConstructed` | `empty` on a queue nobody has enqueued to | `try_dequeue`, or enqueue first |
| `Missing required libraries: reboot.std.collections.v1.sorted_map` | `queue_library()` registered without `sorted_map_library()` | Add `sorted_map_library()` |

## See also

- [`servicer-workflow-loop.md`](servicer-workflow-loop.md) — the consume loop's iteration boundary
- [`servicer-workflow-declare.md`](servicer-workflow-declare.md) — declaring and starting the consumer
- [`lifecycle-initialize-hook.md`](lifecycle-initialize-hook.md) — aliases for calls in `initialize`
