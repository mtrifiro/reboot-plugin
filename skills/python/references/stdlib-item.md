---
title: Use `Item` for Heterogeneous Values in Stdlib Containers
impact: LOW-MEDIUM
impactDescription: Queue/Topic accept Items; picking the right value field affects ergonomics across languages
tags: stdlib, Item, value, bytes, any, Queue, Topic
summary: "A bulk `Item` with two of `value`/`bytes`/`any` stores silently; single calls take one keyword, bulk `items=[...]`; `reboot.protobuf` converts."
step: servicer
applies: [mcp-ui, web-app, backend-only]
always: false
when: "using the stdlib `Item` value envelope"
verified: 1.6.0
docs: ""
---

# Use `Item` for Heterogeneous Values in Stdlib Containers

## When you are here

Putting values into or reading them from a `Queue` or `Topic`. `Item`
(`from reboot.std.item.v1.item import Item`) is their value envelope;
set one of its three optional fields:

| Field | Type | Use for |
| --- | --- | --- |
| `value` | `google.protobuf.Value` | JSON-shaped data; best TypeScript ergonomics |
| `bytes` | `bytes` | Opaque or pre-serialized payloads |
| `any` | `google.protobuf.Any` | A typed message both ends know |

## Do this

Single-item `enqueue` / `publish` take one top-level `value=`,
`bytes=` or `any=`; bulk calls take `items=[Item(...), ...]`. Read back
with `HasField`. `reboot.protobuf` has `from_str` / `as_str` /
`to_json` for `Value`.

```python
from google.protobuf.any_pb2 import Any
from google.protobuf.struct_pb2 import Value
from my.api.v1.things_rbt import Thing
from reboot.protobuf import as_str, from_str
from reboot.std.item.v1.item import Item

await Queue.ref(qid).enqueue(context, value=from_str("hello"))
await Queue.ref(qid).enqueue(context, bytes=b"raw payload")
typed = Any()
typed.Pack(Thing(name="foo"))
await Queue.ref(qid).enqueue(context, any=typed)
# Bulk:
await Queue.ref(qid).enqueue(
    context, items=[Item(value=Value(string_value=s)) for s in batch],
)

batch = await queue.dequeue(context, bulk=True)
for item in batch.items:
    if item.HasField("value"):
        text = as_str(item.value)
    elif item.HasField("bytes"):
        ...
    elif item.HasField("any"):
        ...  # Unpack into your message type
```

## Never

- Two of `value=` / `bytes=` / `any=`, or one plus `items=`, on
  `enqueue` / `publish` — raises `TypeError`.
- `Item(value=..., bytes=...)` in a bulk list — the fields are
  independent `optional`s, not a `oneof`, so it is stored with both set
  and an `if/elif` reader sees only `value`.

## Limits

- The exactly-one check is on the request (`Queue.enqueue`,
  `Topic.publish`), not on `Item` itself (1.6.0 source).
- `any` is only as portable as the schema both ends share.

## Scales as

- Not measured.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| ``TypeError: Only one of `value`, `bytes`, `any`, or `items` should be set`` | Zero or several value keywords on `enqueue` / `publish` | Pass exactly one |

## See also

- [`stdlib-queue.md`](stdlib-queue.md) — producing and consuming items
- [`stdlib-pubsub.md`](stdlib-pubsub.md) — publishing items to topics
