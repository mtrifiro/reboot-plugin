---
title: Get Actor References with `Service.ref(id)`
impact: MEDIUM
impactDescription: Wrong ref construction hits nonexistent actors, aborts readers with `StateNotConstructed`, or raises `AttributeError` / `MixedContextsError`
tags: rpc, ref, actor, identity, state_id, StateNotConstructed, MixedContextsError, existence check
summary: "`self.state_id` raises, use `self.ref().state_id`; probing existence without `StateNotConstructed`; caller-supplied IDs; reserved method names."
step: servicer
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: ""
---

# Get Actor References with `Service.ref(id)`

## When you are here

You need a handle on an actor (possibly your own) to call it or to ask
whether it exists. Arguments: `rpc-calls.md`; constructing:
`rpc-constructor-calls.md`.

## Do this

`Service.ref(id)` returns a typed handle (a `WeakReference`) to the
actor with that string ID; it is cheap, touches no storage, and does
**not** create the actor.

```python
from chat_room.v1.chat_room_rbt import ChatRoom

chat_room = ChatRoom.ref("reboot-chat-room")
await chat_room.send(context, message="Hello!")
```

### Your own actor and its ID

A servicer has no `self.state_id`:

| Context                                                  | Get the actor's state ID via |
| -------------------------------------------------------- | ---------------------------- |
| `ReaderContext` / `WriterContext` / `TransactionContext` | `self.ref().state_id`        |
| `WorkflowContext`                                        | `context.state_id`           |

`self.ref()` also schedules the servicer on itself:
`await self.ref().schedule(when=timedelta(seconds=1)).interest(context)`.

### IDs are caller-supplied strings

Any string the caller chooses: a semantic key (account ID, room name),
one derived from the parent (`f"{self.ref().state_id}-accounts"`, no
stored field, always re-derivable), or a UUID minted once and stored
(`self.state.account_ids_map_id = str(uuid4())`; an `OrderedMap` is
constructed implicitly on its first `insert`).

Minting `uuid4()` in a writer, transaction or constructor and storing
it in the same call is safe: dev-mode effect validation runs the body,
aborts it (discarding every effect, including actors a transaction
constructed), reruns and commits only the second run, never comparing
them (1.6.0 source, `maybe_raise_effect_validation_retry`). A random ID
is a bug only where something re-derives it later: a second call that
recomputes it, or a workflow body outside a memoized step.

### "Does this actor exist?"

A reader on a never-constructed actor **aborts** `StateNotConstructed`
for every type, with or without a `factory=True` constructor (1.6.0
source). Probe by catching the reader's `<Method>Aborted`:

```python
from rbt.v1alpha1.errors_pb2 import StateNotConstructed


async def airport_exists(context, iata: str) -> bool:
    try:
        await Airport.ref(iata).details(context)
    except Airport.DetailsAborted as aborted:
        if not isinstance(aborted.error, StateNotConstructed):
            raise
        return False
    return True
```

A writer on a type with no explicit constructor constructs the actor
implicitly; on a type with a `factory=True` constructor it aborts
`StateNotConstructed` (`requires_constructor: true`).

## Never

- Assume a reader on a missing actor returns zero-valued state — it
  aborts, so "empty field means unknown" validation fails only in the
  negative-path test. Wrap cross-actor reads in the probe unless the
  caller guarantees existence; decide what a failed decorative lookup
  means (default it) first.
- `self.state_id` — `AttributeError: 'XServicer' object has no
  attribute 'state_id'`. Use `self.ref().state_id` (`context.state_id`
  in a workflow).
- `ChatRoomServicer().send(...)` — servicer instances belong to Reboot;
  call through `ChatRoom.ref(id)`.
- One ref used from two contexts (e.g. `program =
  Program.ref("BS-CS")`, called as the registrar and again as a second
  user) — `MixedContextsError` even without concurrency. Keep the ID;
  call `Program.ref(id)` inline per context.
- Expect `Service.create(...)` / a factory on an existing actor to rerun
  its body (`rpc-constructor-calls.md` § Never). A field added to
  the constructor later is never back-filled on existing actors
  (`InvalidStateRefError: The 'state_id' option must be at least 1
  character(s) long` when used as a ref); allocate lazily:
  `if self.state.x == "": ...`.
- Expect the caller's identity to travel through a ref call from inside
  a servicer — it does not (`servicer-authorizer.md`).

## Limits

- Method names `read`, `write`, `delete`, `state`, `schedule`, `spawn`
  are rejected by codegen (they collide with the ref API); `User` also
  reserves `create` and `set_claims`; names may not start with `_`
  (1.6.0 source).
- `Type.ref()` with no ID is legal only inside a workflow (it means the
  workflow's own actor); elsewhere it raises `RuntimeError: \`ref()\`
  called without a \`state_id\` can only be used within a Workflow.`
- Every probe of a missing actor logs a `WARNING ... not constructed`
  line, silenced for 5 minutes per process (1.6.0 source), which can
  drown test output.

## Scales as

- A ref costs nothing; each call is an RPC; an existence probe is a
  full reader call (`patterns-load-and-benchmarking.md`).

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `aborted with 'StateNotConstructed'` | A reader (or, on a factory type, a writer) ran against an actor never constructed | Construct it first, or catch `<Method>Aborted` and check `isinstance(aborted.error, StateNotConstructed)` |
| `aborted with 'StateNotConstructed { requires_constructor: true }'` | A non-constructor writer on a type with a `factory=True` constructor | Call the constructor first |
| `AttributeError: 'XServicer' object has no attribute 'state_id'` | `self.state_id` on a servicer | `self.ref().state_id` / `context.state_id` |
| `MixedContextsError` / `has previously been used by a different \`Context\`` | One `WeakReference` reused across contexts | Fresh `Type.ref(id)` per context |
| `has illegal name: <Name> is reserved`, or only `protoc failed with exit status 1` | A method named `read`, `write`, `delete`, `state`, `schedule` or `spawn` | Rename it; `scripts/api_lint.py` finds it before generate |
| `InvalidStateRefError: The 'state_id' option must be at least 1 character(s) long` | Ref built from an empty stored ID, usually a new ID field never back-filled on an existing actor | Allocate the ID lazily on first use; treat `""` as empty in readers; see Never |
| `State '<id>' for state type '<type>' not constructed (call any writer to construct). Will silence this message for the next 5 minutes.` | A WARNING per probe of a missing actor | Expected when probing existence; construct singletons from `initialize` with a no-op writer |

## See also

- [`rpc-calls.md`](rpc-calls.md) — kwargs, gather, call conventions
- [`rpc-constructor-calls.md`](rpc-constructor-calls.md) — constructing actors, idempotently
- [`servicer-authorizer.md`](servicer-authorizer.md) — nested calls carry no identity
