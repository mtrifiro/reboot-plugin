---
title: Pick the Right Shape for Each Collection
impact: HIGH
impactDescription: Putting an unbounded collection in-state, or flattening an entity into `list[Sub]` when it has its own identity, forces a full data-model rewrite once the app grows.
tags: state, collections, list, dict, OrderedMap, decomposition, cohesion, sub-records, entity, ids
summary: "Decide whether each \"list of X\" item is its own state Type (usually yes), then pick `list[Sub]`, `list[str]` of IDs, or an `OrderedMap`; never `list[Entity]` on a parent."
step: api
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: ""
---

# Pick the Right Shape for Each Collection

## When you are here

The app has "a list of X" and you are choosing how state holds it:
whether X is its own state `Type`, and which container indexes it.
The `OrderedMap` API is in `stdlib-ordered-map.md`; splitting *one* actor by concern is
`state-actor-decomposition.md`; inline sub-records are
`state-nested-models.md` (the MCP-UI corollary is
`mcp-ui/references/api-state-shapes.md`).

## Do this

### Step 1: Decompose, unless the items must change together

The item wants to be its **own state `Type`** if **any** of these holds:

- It has its own lifecycle, or nested collections that grow.
- It has methods you would call on it directly (`Person.add_event(...)`).
- It needs its own authorizer.
- Multiple parents could reference it.
- It is a domain noun (`Person`, `Order`, `Post`, `Message`), not a field
  group (`Address`, `Preferences`, `LineItem`).

A noun with "add / remove / list / show one" is almost always its own
`Type`. "Each user has N of them" = **N actors**.

**Externally-synced collections** (a repo's issues, a mailbox, a feed,
rows from a third-party API) never show an "add" verb, but they are
entity collections and unbounded by definition. Size them to the
**source**, not the demo. Each synced item is its own `Type`, indexed
with Shape C.

**Counter-test: cohesion.** If one user action must change several
items at once, all or none ("hold these 4 seats", "move these 3
cards"), keep the items inline on one actor even when they look
entity-ish. The actor you pick is the lock you get: one actor makes
the action a single serialized `Writer` that validates the whole batch
before mutating; N actors make it an N-party transaction. Group what
must change together; split what must scale independently. (A showing's
200 seats inline as `list[Seat]` held every invariant under 40
concurrent patrons with no app-level locking.)

### Step 2: Pick the container

| Shape | When | Pitfalls |
| --- | --- | --- |
| **A. `list[Sub]` / `dict[str, Sub]` of non-state `Model`s** | No identity of their own; live and die with the parent; bounded (dozens). Line items, tags, config fields. | Every write rewrites the list. No pagination. |
| **B. `list[str]` / `dict[str, str]` of foreign state IDs** | Items are their own `Type`, the collection stays bounded (a few hundred, low thousands at most), and you read the whole index. | Each parent write rewrites the ID list. |
| **C. `OrderedMap` of foreign state IDs** | Items are their own `Type` and the collection is unbounded, or needs pagination, range queries, or ordered iteration. | Extra hop. `value`/`bytes`/`any` envelope. `range` needs `limit=`. |

**"Bounded" is a domain fact, not a knob.** A board has 9 cells; a
building fixes its seat count. An invented `MAX_ITEMS = 40` is Shape C
in disguise: it decides what to *show*, so it belongs in a reader.
B → C later rewrites every method that touches the index; A → B/C
moves every method to another actor. Choose C up front if the collection might grow without bound.

Shape A is `items: list[LineItem]` of plain `Model`s on the parent;
Shape B is `member_user_ids: list[str]`, each member addressable as
`User.ref(user_id)`.

### Shape C: persist the map's ID, allocate it in the constructor

```python
from reboot.std.collections.ordered_map.v1.ordered_map import (
    OrderedMap, ordered_map_library,
)
from uuid import uuid4
from uuid7 import create as uuid7


class UserState(Model):
    # ID of the OrderedMap actor that indexes this user's People.
    # Allocated once at User construction; never changes.
    people_index_id: str = Field(tag=1, default="")


class UserServicer(User.Servicer):

    async def create(self, context: WriterContext) -> None:
        if context.constructor:
            # Just allocate the ID — the OrderedMap is constructed
            # implicitly on the first `insert`. Until then, reading it
            # aborts with `StateNotConstructed`; see
            # `stdlib-ordered-map.md`.
            self.state.people_index_id = str(uuid4())

    async def add_person(
        self,
        context: TransactionContext,
        request: User.AddPersonRequest,
    ) -> User.AddPersonResponse:
        # `Person` is its own state Type with `factory=True` `create`.
        person, _ = await Person.create(
            context,
            name=request.name,
            birthday=request.birthday,
        )
        # UUIDv7 keys give time-ordered iteration for free; for
        # name-sorted iteration, use a name-prefixed key instead.
        await OrderedMap.ref(self.state.people_index_id).insert(
            context,
            key=str(uuid7()),
            bytes=person.state_id.encode(),
        )
        return User.AddPersonResponse(person_id=person.state_id)

    async def list_people(
        self,
        context: ReaderContext,
        request: User.ListPeopleRequest,
    ) -> User.ListPeopleResponse:
        page = await OrderedMap.ref(
            self.state.people_index_id,
        ).range(
            context, start_key=request.cursor, limit=32,
        )
        return User.ListPeopleResponse(
            person_ids=[e.bytes.decode() for e in page.entries],
            next_cursor=(
                page.entries[-1].key if page.entries else ""
            ),
        )
```

Register `ordered_map_library()` in `Application(libraries=[...])`.

**Every cross-`Type` reference is a persisted ID field.** This covers
user-defined types and every stdlib type (`OrderedMap`, `Queue`, `Item`, `Presence`,
`Topic`): a `<thing>_id: str` field on the parent, allocated once in
the constructor, used as `X.ref(self.state.<thing>_id)`. Why: the
schema then documents the actor graph (`rbt inspect`, `/__/inspect`
and the cloud console show state, not servicer source); moving or
sharding the child is one edit, not a grep; and the constructor marks
the moment of ownership instead of the child appearing on whichever
method touches it first.

## Never

- `UserState.people: list[Person]` when `Person` has methods,
  lifecycle or nested events — flattens N actors into one. Promote it
  to a `Type`; use Shape B or C.
- `Type(state=X)` *and* `list[X]` / `dict[str, X]` as a state field —
  the "state inside state" regression (`state-nested-models.md`).
- `list[str]` for an unbounded collection "because it's simpler" —
  the later migration rewrites every method on the parent. Shape C.
- A `MAX_ITEMS` constant so an open-ended or synced collection fits a
  `list` — the cap truncates data; it does not bound the domain. Cap
  the view in a reader.
- An externally-synced collection as `list[Sub]` on one actor — every
  sync rewrites the whole list and the actor grows toward the
  per-actor state-size limit.
- `OrderedMap` for a clearly bounded, sub-dozen collection — wasted
  hop; Shape A or B.
- Splitting items that one action must change together into separate
  `Type`s — turns a single-actor writer into a multi-actor
  transaction. Apply the cohesion counter-test.
- `OrderedMap.ref(f"{self.ref().state_id}-drafts")` (or
  `context.state_id` in a workflow) — runs, but hides the edge from the
  schema and repeats the magic string at every callsite. Persist a
  `<thing>_index_id` field.
- Adding a new `<thing>_index_id` to a type that already has actors and
  allocating it only in the `factory=True` constructor — the
  constructor is a no-op on existing actors, the field stays `""`, and
  `OrderedMap.ref("")` raises `InvalidStateRefError`. Allocate lazily
  in the writer or transaction that first needs it
  (`if self.state.people_index_id == "": ...`) and have readers treat
  `""` as empty; see `api-schema-evolution.md`.

## Limits

- Reading an `OrderedMap` before its first `insert` (or `create`)
  aborts with `StateNotConstructed`; it does not return an empty page.
  Construct up front or catch the abort (`stdlib-ordered-map.md`).
- `OrderedMap.insert` / `create` take a `TransactionContext` (or
  workflow / external context), not a `WriterContext`; the method that
  inserts must be a `Transaction`.
- `uuid4()` in a constructor or transaction is safe under dev-mode
  effect validation at 1.6.0: validation runs the body, aborts it
  (discarding its effects), runs it again and commits only the second
  run; it never compares the two. A random value is fine once persisted
  and read back; it is a bug only when something must *re-derive* it
  later (an idempotency key, a code a caller recomputes). (A 1.4.0
  project reported a constructor `uuid4()` failing validation; the
  1.6.0 source has no comparison step.)
- A per-actor state-size limit bounds Shapes A and B (number not recorded).

## Scales as

- Every write persists the whole actor: a parent holding 8,878 inline
  records re-serialised all of them to bump one integer (measured at
  1.6.0; the cost was state-store load, not wall-clock). Keep large
  collections off frequently written actors.
- Shape B is fine to low thousands of IDs; past that the per-add
  rewrite of the full list becomes noticeable.
- Cost follows the actor boundary: an action inside one actor is one
  serialized writer; across N actors it is an N-participant
  transaction (see `servicer-transaction.md` for participant cost).

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `InvalidStateRefError: The 'state_id' option must be at least 1 character(s) long` | A persisted ID field is still `""` — usually a new field never back-filled on an existing actor | Allocate lazily on first use; treat `""` as empty in readers |
| `aborted with 'StateNotConstructed'` | A read hit an `OrderedMap` (or factory-constructed actor) that was never constructed | Construct it first, or catch `<Method>Aborted` and treat as empty |

## See also

- [`stdlib-ordered-map.md`](stdlib-ordered-map.md) — Shape C API and pagination
- [`state-actor-decomposition.md`](state-actor-decomposition.md) — split one actor by concern
- [`api-schema-evolution.md`](api-schema-evolution.md) — adding fields to live state
