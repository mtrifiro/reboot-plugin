---
title: Compose State with Nested `Model`s
impact: MEDIUM
impactDescription: Flat-only state forces unwieldy parallel field naming as state grows; nesting a *state* Model inside another state Model collapses N actors into one.
tags: state, nested, models, sub-objects, structure
summary: "Group related fields into nested non-state `Model`s instead of parallel flat names, and mutate them in place; never put a state `Model` inside another state `Model`."
step: api
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: ""
---

# Compose State with Nested `Model`s

## When you are here

State has groups of fields that belong together (shipping and billing
addresses). Whether a group is part of this actor or its own actor:
[`state-collections.md`](state-collections.md) (entity collections) and
[`state-actor-decomposition.md`](state-actor-decomposition.md)
(unrelated concerns).

## Do this

Group related fields into a nested **non-state** `Model` instead of
parallel flat names (`shipping_street`, `shipping_city`,
`billing_street`, …):

```python
from typing import Optional

from reboot.api import Field, Model


class Address(Model):
    street: str = Field(tag=1, default="")
    city: str = Field(tag=2, default="")
    zip: str = Field(tag=3, default="")


class OrderState(Model):
    # A single nested `Model` is Optional, `default=None` (`api-pydantic.md`).
    shipping: Optional[Address] = Field(tag=1, default=None)
    billing: Optional[Address] = Field(tag=2, default=None)


# In a writer/transaction: assign a whole sub-model, or set fields one by one.
async def update_shipping(
    self, context: WriterContext, request: Order.UpdateShippingRequest,
) -> None:
    self.state.shipping = Address(
        street=request.street,
        city=request.city,
        zip=request.zip,
    )
```

- Field-by-field assignment needs a guard while the field is `None`
  (`if self.state.shipping is None: ...`).
- `list[Address]` / `dict[str, Address]` use `default_factory=list` /
  `dict`.

## Never

- Use a **state** `Model` (one bound as `state=` in a `Type(...)`) as
  a field of another state `Model`, alone or in a `list`/`dict` —
  collapses separate actors into one. Store the other actor's string ID
  and use `<OtherType>.ref(id)`; the ID container (`list[str]`,
  `dict[str, str]`, a stdlib `OrderedMap`) is in `state-collections.md`.
- Inline items that have their own identity, lifecycle or methods —
  they are a `Type` of their own (same rule, `state-collections.md`).

## Limits

- Protobuf rejects messages nested more than 100 levels deep; a method
  that hits it fails with `Unknown` and a `DecodeError` in the log
  (1.6.0 template).

## Scales as

- A nested `Model` is read and written with the whole actor; see
  `state-collections.md` § Scales as.

## Errors you will see

None known beyond the nested-`Model` default rows in
[`api-pydantic.md`](api-pydantic.md) § Errors you will see.

## See also

- [`state-collections.md`](state-collections.md) — when a group becomes its own actor
- [`api-pydantic.md`](api-pydantic.md) — `Optional` nested-Model default rule
- [`patterns-cross-actor-reads.md`](patterns-cross-actor-reads.md) — read models across actors
