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

The design needs a durable FIFO: a work, job or intake queue, anything
"pulled off a queue". `Queue` (`reboot.std.collections.queue.v1.queue`)
is that primitive: a durable FIFO of `Item` values backed by an internal
stdlib sorted-map actor. Producers `enqueue` from any mutating context;
a workflow consumer `dequeue`s, blocking until items arrive. Do not
define your own queue type or keep a list-as-queue on actor state.
Fan-out to many queues is `stdlib-pubsub.md`; the `Item` envelope is
`stdlib-item.md`.

## Do this

### Methods

| Method | Kind | Notes |
| --- | --- | --- |
| `enqueue` | transaction | exactly one of `value` / `bytes` / `any` (single) or `items: list[Item]` (bulk) |
| `dequeue` | workflow | blocks until at least one item; `bulk: bool`, `at_most?: int` |
| `try_dequeue` | transaction | non-blocking; empty response if nothing is there |
| `empty` | reader | whether the queue holds nothing |

There is no `create`: unlike an `OrderedMap`, a `Queue` builds its
backing sorted map on first use, so producers enqueue straight onto a
ref.

### Register

```python
from reboot.std.collections.queue.v1 import queue
from reboot.std.collections.v1.sorted_map import sorted_map_library


async def main():
    await Application(
        servicers=[ProducerServicer, ConsumerServicer] + queue.servicers(),
        libraries=[sorted_map_library()],
        initialize=initialize,
    ).run()
```

`queue.servicers()` is `[QueueServicer] + sorted_map.servicers()`;
`Application` deduplicates servicers, so also listing
`sorted_map_library()` is harmless. To give the queue an authorizer,
register it as a library instead:
`libraries=[queue_library(authorizer=...), sorted_map_library()]`
(`queue_library` from the same module; it requires the sorted-map
library). Never reach for the sorted-map types in application code; a
user-facing sorted collection is `OrderedMap` (`stdlib-ordered-map.md`).

### Produce

```python
from reboot.std.collections.queue.v1.queue import Queue
from reboot.std.item.v1.item import Item


class ProducerServicer(Producer.Servicer):

    async def submit(
        self, context: TransactionContext, request: SubmitRequest,
    ) -> SubmitResponse:
        await Queue.ref(WORK_QUEUE_ID).enqueue(
            context, value=request.payload,
        )
        return SubmitResponse()
```

Bulk: `await Queue.ref(WORK_QUEUE_ID).enqueue(context, items=[Item(value=p) for p in payloads])`.

### Consume in a workflow, started from `initialize`

```python
from reboot.aio.contexts import WorkflowContext
from reboot.aio.external import InitializeContext
from reboot.std.collections.queue.v1.queue import Queue


class ConsumerServicer(Consumer.Servicer):

    @classmethod
    async def control_loop(
        cls, context: WorkflowContext, request,
    ):
        queue = Queue.ref(f"{context.state_id}-work")

        async for iteration in context.loop("Consume"):
            response = await queue.per_iteration(
                "Dequeue work",
            ).dequeue(context, bulk=True)
            for item in response.items:
                # `item.value`, `item.bytes`, or `item.any` —
                # whichever was set at enqueue time.
                ...


async def initialize(context: InitializeContext):
    await Consumer.ref(CONSUMER_ID).idempotently(
        "Start consumer",
    ).spawn().control_loop(context)
```

`dequeue` blocks the workflow until at least one item is there; no
polling. `bulk=True` returns up to `DEFAULT_BULK_COUNT` (64) items;
`at_most=N` caps the batch. The `"Start consumer"` alias is required in
`initialize`, and it is what stops each boot from starting another
consumer beside the last one. From a transaction, start it with
`Consumer.ref(id).schedule().control_loop(context)` instead
(`servicer-workflow-declare.md`).

### Try-dequeue from a transaction

```python
response = await Queue.ref(WORK_QUEUE_ID).try_dequeue(
    context, bulk=True, at_most=10,
)
```

Same response shape as `dequeue`; an empty queue returns no items
instead of blocking.

## Never

- `Queue.ref(id).create(context)` — `Queue` has no constructor
  (`'WeakReference' object has no attribute 'create'`). Enqueue
  directly; the backing map is built on first use.
- `dequeue` from a writer or transaction — it is a workflow method;
  call it from a `WorkflowContext`, or use `try_dequeue`.
- A bare `.spawn()` of the consumer from `initialize` — raises
  `IdempotencyRequiredError`; use `.idempotently("alias").spawn()`.
- Reading `empty` on a queue that may never have been enqueued to —
  it aborts `StateNotConstructed` (observed at 1.6.0), and a workflow
  doing it retries forever. Use `try_dequeue` (returns empty on an
  unused queue) or a blocking `dequeue`, or enqueue once before reading.
- Calling `try_dequeue` twice on the same queue from one `until`
  callable — the second call is refused without an alias; see
  `servicer-workflow-wait.md`.
- Hand-rolling a queue as a list field on actor state.

## Limits

- `QueueServicer`'s default authorizer is
  `allow_if(all=[is_app_internal])`: only your own servicers can
  enqueue/dequeue. Browsers and MCP clients go through your methods, or
  you pass `queue_library(authorizer=...)`.
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
