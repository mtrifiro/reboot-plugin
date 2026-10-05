---
title: API State Shapes — List and Nested Sub-Objects
impact: HIGH
impactDescription: Two recurring MCP UI state patterns. `list[Item]` of non-state Models is for **bounded sub-records** that have no identity of their own; entity collections (people, posts, messages, anything addressable on its own) must be promoted to their own state `Type`. Single nested `Model` sub-objects must be `Optional` with `default=None` and hydrated in the factory `create` Writer.
tags: state, list, nested, sub-object, optional, model, default, default_factory, decomposition, crud
summary: "`list[Item]` only for bounded sub-records without identity, with index-checked CRUD Writers; a single nested `Model` is `Optional` and hydrated in factory `create`; never nest state Models."
step: api
applies: [mcp-ui]
always: false
verified: 1.6.0
docs: ""
---

# API State Shapes — List and Nested Sub-Objects

## When you are here

You are giving an MCP UI application type a list of sub-records or a
single nested sub-object. Almost all of the rules are framework-wide and
live in the python skill — read those first:
[`state-collections.md`](../../python/references/state-collections.md)
decides between in-state `list[Sub]`, a `list[str]` of foreign IDs, and
an `OrderedMap` of IDs (and when to decompose into its own `Type`);
[`api-pydantic.md`](../../python/references/api-pydantic.md) has the
`Optional[X] = None` rule for a nested `Model` and its two startup
errors. This file keeps only the conventions MCP UI apps add on top: the
CRUD Writer set for a bounded list, and hydrating a nested sub-object in
the factory `create` so the React UI never sees `None`.

## Do this

### Bounded sub-record list (Shape A only)

Only when the domain bounds the list (line items on an order, tags on a
post) and the items have no identity of their own:

- Define the item as a standalone `class LineItem(Model)` — not nested
  on the application type — and import it in the servicer standalone:
  `from <pkg>.v1.<name> import LineItem`.
- `items: list[LineItem] = Field(tag=N, default_factory=list)`.
- Add CRUD Writers as needed: `add`, `remove`, `toggle`, `reorder`.
  Each validates its indices before mutating; `reorder` is `pop` +
  `insert`. From React the fields are camelCase:
  `await myType.reorderItem({ fromIndex: 0, toIndex: 1 })`.

### Single nested sub-object: hydrate in factory `create`

```python
from reboot.api import Field, Model
from typing import Optional

class GuestPreferences(Model):
    meal_type: str = Field(tag=1, default="")
    calorie_level: str = Field(tag=2, default="")
    dietary_restrictions: str = Field(tag=3, default="")

class Guest(Model):
    name: str = Field(tag=1, default="")
    # Single nested Model: Optional + default=None, populated by the
    # factory `create` below.
    preferences: Optional[GuestPreferences] = Field(tag=2, default=None)


# Servicer side (in `backend/src/servicers/<name>.py`):
class GuestServicer(Guest.Servicer):
    async def create(
        self, context, *, name, meal_type, calorie_level, dietary_restrictions,
    ):
        self.state.name = name
        self.state.preferences = GuestPreferences(
            meal_type=meal_type,
            calorie_level=calorie_level,
            dietary_restrictions=dietary_restrictions,
        )
```

Plural sub-objects ("each guest's preferences") are a
`list[GuestPreferences]` with `default_factory=list`; lists are exempt
from the `Optional` rule.

## Never

- `list[Item]` for an entity collection (`Person`, `Post`, `Message`,
  `Task`, anything with its own identity, lifecycle or methods) — it
  works in a 10-row demo and falls over as it grows or items need their
  own auth/methods. Give the item its own `Type` and store IDs
  ([`state-collections.md`](../../python/references/state-collections.md)).
- A `MAX_ITEMS` cap to keep a collection small enough for `list[Sub]` —
  a cap you had to add means the collection is unbounded. A collection
  synced or scraped from an external system (issues, mail, a feed) is
  never Shape A; it is an `OrderedMap` of IDs.
- `OrderedMap.ref(f"{self.ref().state_id}-items")` — persist the map's
  ID as a field allocated once in the constructor (`items_index_id`);
  rule and code in `state-collections.md`.
- A state `Model` (one registered as `Type(state=X)`) as a field, or a
  `list[<StateModel>]`, on another state `Model` — store its string ID
  and reach it with `<Type>.ref(id)`
  ([`state-nested-models.md`](../../python/references/state-nested-models.md)).
- A non-`Optional` nested `Model` field with `default=` or
  `default_factory=` — rejected at startup; errors in
  [`api-pydantic.md`](../../python/references/api-pydantic.md).

## Limits

- Every write to a Shape A list rewrites the whole list; there is no
  pagination (`state-collections.md`).

## Scales as

- Not measured.

## Errors you will see

None known beyond those in `api-pydantic.md` and `state-collections.md`.

## See also

- [`state-collections.md`](../../python/references/state-collections.md) — pick the collection shape
- [`api-pydantic.md`](../../python/references/api-pydantic.md) — nested Model defaults, errors
- [`react-app-tsx.md`](react-app-tsx.md) — many actors in one UI
