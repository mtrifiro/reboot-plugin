---
title: Use `Item` for Heterogeneous Values in Stdlib Containers
impact: LOW-MEDIUM
impactDescription: Queue/Topic accept Items; picking the right value field affects ergonomics across languages
tags: stdlib, Item, value, bytes, any, Queue, Topic
summary: "Set exactly one of `value`, `bytes` or `any` per `Item` (a bulk `Item` with two is stored silently); single calls take one top-level keyword, bulk calls `items=[...]`; `reboot.protobuf` converts values."
step: servicer
applies: [mcp-ui, web-app, backend-only]
always: false
when: "using the stdlib `Item` value envelope"
verified: 1.6.0
docs: ""
---

# Use `Item` for Heterogeneous Values in Stdlib Containers

## When you are here

You are putting values into, or reading them out of, a `Queue` or
`Topic`. `Item` (`from reboot.std.item.v1.item import Item`) is their
value envelope. It has three optional fields; set one:

| Field | Type | When to use |
| --- | --- | --- |
| `value` | `google.protobuf.Value` | JSON-shaped data (numbers, strings, lists, dicts, bools). Best ergonomics in TypeScript and for ad-hoc structures. |
| `bytes` | `bytes` | Opaque payloads: raw binary or pre-serialized data. |
| `any` | `google.protobuf.Any` | A typed wire-format message both ends know. |

## Do this

Single-item `enqueue` / `publish` take one top-level `value=`,
`bytes=` or `any=` keyword; bulk calls take `items=[Item(...), ...]`.

```python
from google.protobuf.any_pb2 import Any
from google.protobuf.struct_pb2 import Value
from my.api.v1.things_rbt import Thing
from reboot.std.collections.queue.v1.queue import Queue
from reboot.std.item.v1.item import Item

# Single item — exactly one keyword:
await Queue.ref(qid).enqueue(context, value=Value(string_value="hello"))
await Queue.ref(qid).enqueue(context, bytes=b"raw payload")

typed = Any()
typed.Pack(Thing(name="foo"))
await Queue.ref(qid).enqueue(context, any=typed)

# Bulk:
items = [Item(value=Value(string_value=s)) for s in batch]
await Queue.ref(qid).enqueue(context, items=items)
```

Read items back with `HasField`; each carries the field set at enqueue
time:

```python
batch = await queue.dequeue(context, bulk=True)
for item in batch.items:
    if item.HasField("value"):
        ...  # google.protobuf.Value
    elif item.HasField("bytes"):
        ...  # bytes
    elif item.HasField("any"):
        ...  # google.protobuf.Any — Unpack into your message type
```

`reboot.protobuf` has `from_str` / `as_str` / `to_json` for `Value`
conversions:

```python
from reboot.protobuf import as_str, from_str

await Topic.ref(tid).publish(context, value=from_str(message_id))

batch = await queue.dequeue(context, bulk=True)
ids = [as_str(item.value) for item in batch.items]
```

## Never

- Passing two of `value=` / `bytes=` / `any=`, or one of them plus
  `items=`, to `enqueue` / `publish` — raises `TypeError`. Pick one.
- `Item(value=..., bytes=...)` in a bulk list — the fields are
  independent `optional`s, not a protobuf `oneof`, so nothing rejects
  it: the item is stored with both set, and an `if/elif` reader sees
  only `value`. Set one field per item.

## Limits

- The exactly-one check is on the request (`Queue.enqueue`,
  `Topic.publish`), not on `Item` itself (1.6.0 source).
- `any` payloads are only as portable as the message schema both ends
  share.

## Scales as

- Not measured.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| ``TypeError: Only one of `value`, `bytes`, `any`, or `items` should be set`` | Zero or several value keywords on `enqueue` / `publish` | Pass exactly one |

## See also

- [`stdlib-queue.md`](stdlib-queue.md) — producing and consuming items
- [`stdlib-pubsub.md`](stdlib-pubsub.md) — publishing items to topics
