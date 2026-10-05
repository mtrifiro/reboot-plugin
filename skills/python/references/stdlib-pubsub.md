---
title: Use `Topic` for Publish/Subscribe Fan-Out to Queues
impact: MEDIUM
impactDescription: Pub/sub fan-out without `Topic` requires hand-rolling broadcast and per-subscriber buffers
tags: stdlib, Topic, pubsub, publish, subscribe, broker, fan-out
summary: "`Topic` fans published `Item`s out to subscribed `Queue`s: register the library, subscribe a queue first (items published with no subscriber are dropped), publish, consume on the queue side."
step: servicer
applies: [mcp-ui, web-app, backend-only]
always: false
when: "publishing to topics (pub/sub)"
verified: 1.6.0
docs: ""
---

# Use `Topic` for Publish/Subscribe Fan-Out to Queues

## When you are here

One producer's items must reach several consumers. `Topic`
(`reboot.std.pubsub.v1.pubsub`) is pub/sub built on `Queue`: publishers
`publish` to the topic; each subscriber owns a `Queue` it registered
with `subscribe`; an internal `broker` workflow copies every published
item into every subscribed queue. `publish` alone delivers nothing:
build both sides. The consumer loop itself is `stdlib-queue.md`.

## Do this

### Methods

| Method | Kind | Notes |
| --- | --- | --- |
| `publish` | writer | exactly one of `value` / `bytes` / `any` (single) or `items: list[Item]` (bulk) |
| `subscribe` | writer | `queue_id: str` — the `Queue` that will receive items; repeating it is a no-op |
| `broker` | workflow | internal; scheduled by the first `publish` or `subscribe` |

### Register

```python
from reboot.std.pubsub.v1 import pubsub
from reboot.std.collections.v1.sorted_map import sorted_map_library


async def main():
    await Application(
        servicers=[MyServicer] + pubsub.servicers(),
        libraries=[sorted_map_library()],
    ).run()
```

`pubsub.servicers()` returns `[TopicServicer] + queue.servicers()`
(which already includes the sorted-map servicer; duplicates are
deduplicated). The library form, which takes an `authorizer=`, needs
its whole chain:
`libraries=[pubsub_library(...), queue_library(), sorted_map_library()]`.

### Subscribe a queue, then publish

```python
from reboot.std.collections.queue.v1.queue import Queue
from reboot.std.pubsub.v1.pubsub import Topic


class SubscriberServicer(Subscriber.Servicer):

    async def attach(
        self, context: WriterContext, request: AttachRequest,
    ) -> AttachResponse:
        # A Queue needs no create; subscribing its ID is enough.
        queue_id = f"{self.ref().state_id}-inbox"
        await Topic.ref(request.topic_id).subscribe(
            context, queue_id=queue_id,
        )
        return AttachResponse()


# Producer side, from any writer / transaction / workflow:
await Topic.ref(topic_id).publish(context, value=some_value)
```

### Consume on the subscriber side

```python
@classmethod
async def control_loop(
    cls, context: WorkflowContext, request,
):
    queue = Queue.ref(f"{context.state_id}-inbox")
    async for iteration in context.loop("Consume"):
        batch = await queue.per_iteration("Dequeue inbox").dequeue(
            context, bulk=True,
        )
        for item in batch.items:
            ...
```

Use one stable topic ID per logical channel (e.g. `f"{room_id}-events"`);
publishers and subscribers must agree on it.

## Never

- Publishing with no consumer side — nothing reads the topic itself.
- Consuming from the topic directly — each subscriber consumes from its
  **own** `Queue`.
- Starting `broker` yourself — the first `publish`/`subscribe`
  schedules it.
- `PubSub.ref(...)` or `subscribe(context, topic=..., queue_id=...)` —
  the 1.6.0 type is `Topic`, and `subscribe` takes only `queue_id`; the
  topic is the actor ID.

## Limits

- Items published while no queue is subscribed are dropped: the broker
  takes every buffered item and enqueues it to the queues subscribed at
  that moment (1.6.0 source). Subscribe before publishing anything that
  matters.
- Delivery to each queue is one `Queue.enqueue` per broker iteration,
  run concurrently across queues.
- There is no `unsubscribe` method at 1.6.0.
- `TopicServicer`'s default authorizer is `allow()` (anyone may publish
  or subscribe), unlike `Queue`'s app-internal default. Pass
  `pubsub_library(authorizer=...)` to restrict it.
- `publish` takes exactly one of `value`, `bytes`, `any`, `items`;
  anything else raises `TypeError` (`stdlib-item.md`).

## Scales as

- Not measured. Each broker iteration writes every buffered item into
  every subscribed queue, so cost grows with items × subscribers.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `Missing required libraries: reboot.std.collections.queue.v1.queue` | `pubsub_library()` without `queue_library()` | Add `queue_library()` and `sorted_map_library()` |

## See also

- [`stdlib-queue.md`](stdlib-queue.md) — the subscriber's consume loop
- [`stdlib-item.md`](stdlib-item.md) — the published value envelope
- [`servicer-workflow-loop.md`](servicer-workflow-loop.md) — per-iteration scope in loops
