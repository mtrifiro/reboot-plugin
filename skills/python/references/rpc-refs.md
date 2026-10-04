---
title: Get Actor References with `Service.ref(id)`
impact: MEDIUM
impactDescription: Wrong ref construction hits nonexistent actors, aborts readers with `StateNotConstructed`, or raises `AttributeError` / `MixedContextsError`
tags: rpc, ref, actor, identity, state_id, StateNotConstructed, MixedContextsError, existence check
step: servicer
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: ""
---

# Get Actor References with `Service.ref(id)`

## When you are here

You are inside a servicer (or a test or `initialize`) and need a handle
on an actor, possibly your own, to call a method on it, or to ask
whether it exists yet. How to pass arguments is in `rpc-calls.md`;
constructing an actor is in `rpc-constructor-calls.md`.

## Do this

`Service.ref(id)` returns a typed handle (a `WeakReference`) to the
actor with that string ID. It is cheap, does not touch storage, and
does **not** create the actor.

```python
from chat_room.v1.chat_room_rbt import ChatRoom

chat_room = ChatRoom.ref("reboot-chat-room")
await chat_room.send(context, message="Hello!")
```

### Your own actor and its ID

A servicer instance has no `self.state_id`. Get the ID from the ref or
the context, depending on the method kind:

| Context                                                  | Get the actor's state ID via |
| -------------------------------------------------------- | ---------------------------- |
| `ReaderContext` / `WriterContext` / `TransactionContext` | `self.ref().state_id`        |
| `WorkflowContext`                                        | `context.state_id`           |

```python
async def tick(self, context: WriterContext, request) -> None:
    rng = random.Random(hash((self.ref().state_id, ...)))

@classmethod
async def control_loop(cls, context: WorkflowContext, request):
    queue = Queue.ref(f"{context.state_id}-messages-queue")
    ...
```

`self.ref()` is also how a servicer schedules itself:

```python
async def open(
    self, context: WriterContext, request: OpenRequest,
) -> OpenResponse:
    await self.ref().schedule(when=timedelta(seconds=1)).interest(context)
    return OpenResponse()
```

### IDs are caller-supplied strings

The ID is whatever string the caller chooses: a semantic key (account
ID, room name), an ID derived from the parent
(`f"{self.ref().state_id}-accounts"`, which needs no stored field and
can always be re-derived), or a UUID minted at creation and stored:

```python
from uuid import uuid4

self.state.account_ids_map_id = str(uuid4())
# OrderedMap is constructed implicitly on the first `insert`.
```

Minting `uuid4()` inside a writer, transaction or constructor and
storing it in the same call is safe. Dev-mode effect validation runs
the body, aborts it (discarding every effect, including actors a
transaction constructed), runs it again and commits only the second
run; it never compares the two runs (1.6.0 source,
`maybe_raise_effect_validation_retry`). A random ID is a bug only where
something must re-derive it later: a second call that recomputes it, or
a workflow body outside a memoized step.

### "Does this actor exist?"

A reader on an actor that was never constructed **aborts** with
`StateNotConstructed`, for every type, with or without a `factory=True`
constructor (1.6.0 source: any reader on missing state raises it).
Probe by catching the reader's `<Method>Aborted`:

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

A writer on a type with no explicit constructor implicitly constructs
the actor and proceeds. On a type that has a `factory=True`
constructor, a non-constructor writer also aborts with
`StateNotConstructed` (`requires_constructor: true`): only the
constructor brings it into existence.

## Never

- Assume a reader on a missing actor returns zero-valued state — it
  aborts with `StateNotConstructed`. A validation path built on "empty
  field means unknown" fails only in the negative-path test. Wrap
  cross-actor reads in the probe above unless the caller guarantees
  existence, and decide what a failed decorative lookup means
  (default it) before deciding what it returns.
- `self.state_id` — raises `AttributeError: 'XServicer' object has no
  attribute 'state_id'`. Use `self.ref().state_id` (or
  `context.state_id` in a workflow).
- `ChatRoomServicer().send(...)` — servicer instances belong to Reboot.
  Call through `ChatRoom.ref(id)`.
- Hold one ref and use it from two contexts (e.g. `program =
  Program.ref("BS-CS")`, then call as the registrar's context and again
  as a second user's) — raises `MixedContextsError` even with no
  concurrency. Keep the ID; call `Program.ref(id)` inline per context.
- Expect `Service.create(...)` / a factory on an existing actor to run
  its body again — a repeat with a fresh key aborts with
  `StateAlreadyConstructed`; a repeat with a key already used
  (`initialize`'s automatic per-(actor, method) key, or the same
  `.idempotently(alias)`) returns the memoized result without running
  the body. A field added to the constructor later is never
  back-filled on existing actors (`InvalidStateRefError: The 'state_id'
  option must be at least 1 character(s) long` when it is used as a
  ref). Allocate such a field lazily: `if self.state.x == "": ...`.
- Expect the caller's identity to travel through a ref call from
  inside a servicer — it does not; see `servicer-authorizer.md`.

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

- A ref costs nothing; each call through it is an RPC. An existence
  probe is a full reader call (see
  `patterns-load-and-benchmarking.md`).

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `aborted with 'StateNotConstructed'` | A reader (or, on a factory type, a writer) ran against an actor never constructed | Construct it first, or catch `<Method>Aborted` and check `isinstance(aborted.error, StateNotConstructed)` |
| `aborted with 'StateNotConstructed { requires_constructor: true }'` | A non-constructor writer on a type with a `factory=True` constructor | Call the constructor first |
| `aborted with 'StateAlreadyConstructed'` | An explicit constructor called on an actor that exists | Probe first, or call it via `.idempotently(...)` |
| `AttributeError: 'XServicer' object has no attribute 'state_id'` | `self.state_id` on a servicer | `self.ref().state_id` / `context.state_id` |
| `MixedContextsError` / `has previously been used by a different \`Context\`` | One `WeakReference` reused across contexts | Fresh `Type.ref(id)` per context |
| `has illegal name: Schedule is reserved` | A method named after a ref API verb | Rename the method |
| `InvalidStateRefError: The 'state_id' option must be at least 1 character(s) long` | Ref built from an empty stored ID | Allocate the ID lazily; see Never |

## See also

- [`rpc-calls.md`](rpc-calls.md) — kwargs, gather, call conventions
- [`rpc-constructor-calls.md`](rpc-constructor-calls.md) — constructing actors, idempotently
- [`servicer-authorizer.md`](servicer-authorizer.md) — nested calls carry no identity
