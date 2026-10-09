---
title: API State Shapes — List and Nested Sub-Objects
impact: HIGH
impactDescription: Two recurring MCP UI state patterns. `list[Item]` of non-state Models is for **bounded sub-records** that have no identity of their own; entity collections (people, posts, messages, anything addressable on its own) must be promoted to their own state `Type`. Single nested `Model` sub-objects must be `Optional` with `default=None` and hydrated in the factory `create` Writer.
tags: state, list, nested, sub-object, optional, model, default, default_factory, decomposition, crud
summary: "Never nest state Models; `list[Item]` only for bounded identity-less sub-records; a nested `Model` is `Optional`, hydrated in `create`."
step: api
applies: [mcp-ui]
always: false
verified: 1.6.0
docs: ""
---

# API State Shapes — List and Nested Sub-Objects

## When you are here

Giving an MCP UI application type a list of sub-records or one nested
sub-object. Framework rules live in the python skill — read them first:
[`state-collections.md`](../../python/references/state-collections.md)
(in-state `list[Sub]` vs `list[str]` of foreign IDs vs an `OrderedMap` of
IDs, and when to decompose into its own `Type`);
[`api-pydantic.md`](../../python/references/api-pydantic.md) (the
`Optional[X] = None` rule for a nested `Model`, its two startup errors).
Here: the MCP UI CRUD Writer set for a bounded list, and hydrating a
nested sub-object in factory `create` so React never sees `None`.

## Do this

### Bounded sub-record list (Shape A only)

Only when the domain bounds the list (line items on an order, tags on a
post) and items have no identity:

- Define the item standalone, `class LineItem(Model)`, not nested on the
  type; import it standalone in the servicer:
  `from <pkg>.v1.<name> import LineItem`.
- `items: list[LineItem] = Field(tag=N, default_factory=list)`.
- CRUD Writers as needed — `add`, `remove`, `toggle`, `reorder` — each
  validating indices before mutating; `reorder` is `pop` + `insert`.
  React calls are camelCase:
  `await myType.reorderItem({ fromIndex: 0, toIndex: 1 })`.

### Single nested sub-object: hydrate in factory `create`

```python
from reboot.api import Field, Model
from typing import Optional

class GuestPreferences(Model):
    meal_type: str = Field(tag=1, default="", description="The meal the guest chose, e.g. vegetarian.")
    calorie_level: str = Field(tag=2, default="", description="Low, regular or high.")
    dietary_restrictions: str = Field(
        tag=3, default="", description="Allergies and exclusions, as the guest wrote them.",
    )

class Guest(Model):
    name: str = Field(tag=1, default="", description="The guest's full name.")
    # Optional + default=None; populated by factory `create`.
    preferences: Optional[GuestPreferences] = Field(
        tag=2, default=None, description="Meal preferences; None until `create` fills them.",
    )


# Servicer (`backend/src/servicers/<name>.py`):
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

Plural sub-objects are `list[GuestPreferences]` with
`default_factory=list`; lists are exempt from the `Optional` rule.

## Never

- `list[Item]` for an entity collection (`Person`, `Post`, `Message`,
  `Task`, anything with its own identity, lifecycle or methods) — fine in
  a 10-row demo, fails as it grows or items need their own auth/methods.
  Give the item its own `Type` and store IDs
  ([`state-collections.md`](../../python/references/state-collections.md)).
- A `MAX_ITEMS` cap to keep a collection small enough for `list[Sub]` —
  needing a cap means it is unbounded; a synced or scraped collection is
  an `OrderedMap` of IDs (`state-collections.md` § Never).
- `OrderedMap.ref(f"{self.ref().state_id}-items")` — persist the map's ID
  in a field allocated once in the constructor (`items_index_id`); see
  `state-collections.md`.
- A state `Model` (one registered as `Type(state=X)`) as a field, or a
  `list[<StateModel>]`, on another state `Model` — store its string ID,
  reach it with `<Type>.ref(id)`
  ([`state-nested-models.md`](../../python/references/state-nested-models.md)).
- A non-`Optional` nested `Model` field with `default=` or
  `default_factory=` — rejected at startup; errors in
  [`api-pydantic.md`](../../python/references/api-pydantic.md).

## Limits

- Every write to a Shape A list rewrites the whole list; no pagination
  (`state-collections.md`).

## Scales as

- Not measured.

## Errors you will see

None beyond `api-pydantic.md` and `state-collections.md`.

## See also

- [`state-collections.md`](../../python/references/state-collections.md) — pick the collection shape
- [`api-pydantic.md`](../../python/references/api-pydantic.md) — nested Model defaults, errors
- [`react-app-tsx.md`](react-app-tsx.md) — many actors in one UI
