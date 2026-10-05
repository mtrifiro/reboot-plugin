---
title: Define APIs in Pydantic
impact: CRITICAL
impactDescription: The pydantic API file is the source of truth; everything else is generated from it
tags: pydantic, api, Model, Field, tag, default, Optional, Type, API, description, generated names
summary: "Every `Field` needs a tag and a zero-value default (non-zero is rejected at import time); wire declarations through `API(...)`; generated Request/Response names come from the method name, not the class."
step: api
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: ""
---

# Define APIs in Pydantic

## When you are here

You are writing the pydantic API file under `api/`: the `Model`s for
state, requests, responses and errors, and the `API(...)` block that
binds them to types. `rbt generate` turns it into `<name>_rbt.py` with
`<Type>`, `<Type>.Servicer`, `<Type>.ref(id)` and the nested
request/response names. Choosing method factories and their options is
in [`api-methods.md`](api-methods.md).

## Do this

From [`reboot-bank-pydantic`](https://github.com/reboot-dev/reboot-bank-pydantic),
`api/bank/v1/account.py` (methods abridged; see `api-methods.md`):

```python
from reboot.api import API, Field, Methods, Model, Reader, Type, Writer


class AccountState(Model):
    """One customer's account: the balance and nothing derived from it."""

    balance: float = Field(
        tag=1,
        default=0.0,
        description="What the account holds, in dollars: every deposit "
        "added and every withdrawal and transfer out taken away, and "
        "never below zero.",
    )


class BalanceResponse(Model):
    amount: float = Field(
        tag=1,
        default=0.0,
        description="The balance at the moment of the read, in dollars.",
    )


class DepositRequest(Model):
    amount: float = Field(
        tag=1,
        default=0.0,
        description="How much to add, in dollars; any amount is accepted.",
    )


AccountMethods = Methods(
    balance=Reader(
        request=None,
        response=BalanceResponse,
        description="The funds currently available to withdraw.",
        mcp=None,
    ),
    deposit=Writer(
        request=DepositRequest,
        response=None,
        description="Add funds. Any amount is accepted.",
        mcp=None,
    ),
)


api = API(
    Account=Type(
        state=AccountState,
        methods=AccountMethods,
        description="One customer's money, and the consistency "
        "boundary for every change to it.",
    ),
)
```

The rules, all enforced at import or generate time:

- **Every `Field` has a `tag`**, unique within its `Model`: the
  wire-level field number. Data is keyed by tag.
- **Every `Field` has an explicit default, and it is the type's zero
  value**: `""`, `0`, `0.0`, `False`; `default_factory=list` /
  `default_factory=dict` for collections; for a `Literal`, its first
  value. Real starting values are set at write time, in the
  constructor (`state-scalar-fields.md`).
- **A single nested `Model` field is `Optional[X] = Field(tag=N, default=None)`**,
  set in the constructor or lazily on first write. `list[X]` and
  `dict[str, X]` of a `Model` use `default_factory` like any collection.
- **Every `Field` has a `description=`** saying what the value means,
  its unit and any invariant, not its type. The dashboard shows it
  beside the property, and a missing one as "No description provided,
  please ask your friendly coding agent to add one for you." A
  `Model`'s class docstring becomes the model's description there too.
  Add the description in the same change that adds the field.
- **`Type(description=...)`** says what the state type is _for_: what
  it is the consistency boundary for, what one instance corresponds
  to, how its ID is chosen; not a restatement of its fields.
- **Everything reaches the generator through `API(...)`**: a `Type`
  binds `state=` and `methods=` under a public name.

### Generated names come from the **method** name

For each method, the generated module exposes
`<Type>.<MethodPascalCase>Request` and
`<Type>.<MethodPascalCase>Response`, whatever the class you passed to
`request=` / `response=` is called. Method `create_checkers_game` on
`User` gives `User.CreateCheckersGameResponse`, even if the class is
`SomethingElseEntirely`. Servicers and callers use these names; a
method with `request=None` / `response=None` drops the parameter /
returns `None` (signature in `api-methods.md`).

The name is an alias of the **same class**, not a copy (1.6.0
template: `<Method>Response: TypeAlias = api.<Type>.methods['<method>'].response`).
So one `Model` can be one method's `response=` and the element type of
another's `list[...]` with no envelope Model.

## Never

- `board: str = Field(tag=1)` with no default — the initial state is
  built with `model_construct()`, which skips undeclared defaults; the
  first read raises `AttributeError: 'GameState' object has no
  attribute 'board'`.
- `turn: str = Field(tag=1, default="r")`, `default=1.0`, `default=2` —
  rejected at import. Zero default; set `"r"` in the constructor.
- `Field(tag=N, default_factory=AccountCard)` or
  `Field(tag=N, default=AccountCard())` for a nested `Model` — both
  refused; use `Optional[AccountCard] = Field(tag=N, default=None)`.
- `history: list[str] = Field(tag=3, default=[])` — use
  `default_factory=list`.
- `User.CreateGameResponse` for method `create_checkers_game` —
  `AttributeError: type object 'User' has no attribute
  'CreateGameResponse'`. PascalCase the method name exactly.
- `description="The balance."` — restates the annotation; say what
  the number is and what is true of it.
- `Model`s or a `Type` defined but never wired into `API(...)` — they
  never reach the generator, with no error.

## Limits

- Why only zero defaults: the wire format has nowhere to store a
  per-field default, so a non-zero `default=` could not survive a
  round trip; codegen refuses it rather than silently ignore it.
- `Optional[...]` fields take only `default=None`. Discriminated
  unions take no `default`.
- Field types: `str`, `int`, `float`, `bool`, string `Literal`s,
  `Optional[...]`, `Model`s, discriminated unions, `list[...]`, and
  `dict` with **`str` keys only** (`dict[str, Any]` carries free JSON)
  (1.6.0 source). **`bytes` is not a field type**: `default=b""` is
  refused, and `Optional[bytes]` fails with the empty
  `Failed to import schema file: `. Store base64 in a `str`.
- A package (one `api/<pkg>/v1/*.py`) with `Model`s but no `Type`
  generates nothing, without a warning (observed at 1.6.0).
- A `Model` defined in one API package and used in another (e.g. in
  `errors=[...]`) generates Python that refers to it without importing
  it: `rbt generate` exits 0, then import fails with
  `NameError: name 'common' is not defined` (observed at 1.6.0).
  Workaround: put shared fields in a plain module under `api/` with no
  `API(...)` (it generates nothing) and give each package its own
  empty-body subclass. The copies are distinct types: anything crossing
  a package converts by value, and one is not a declared error of a
  method that declares the other.

## Scales as

- Not measured.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `AttributeError: '` … `' object has no attribute '` | A `Field` without a default, read before it was set | Add the zero default |
| `` uses `default` with an unsupported value. Supported default value for `` | Non-zero default | Zero default; set the value in the constructor |
| `` is a non-optional `Model` type and cannot have a `default` value. Use `Optional` for `Model` types with empty default. `` | `default=` on a nested `Model` | `Optional[X] = Field(tag=N, default=None)` |
| `` uses `default_factory` which is not supported for type `` | `default_factory=` on a non-collection, e.g. a nested `Model` | Same as above |
| `` type and cannot have a `default` value. Use `default_factory` instead. `` | `default=[]` / `default={}` | `default_factory=list` / `dict` |
| `` is `Optional` and uses `default` with a non-None value. `` | `Optional` field with a non-`None` default | `default=None` |
| `` uses `default` which is not supported for type `bytes` `` | A `bytes` field | Base64 in a `str` |
| `Failed to import schema file:` (nothing after) | Often an unsupported field type such as `Optional[bytes]` | Use a supported type |
| `Missing tag for property '` | `Field` without `tag=` | Add a unique tag |
| `Trying to use tag '` … `already used by '` | Duplicate tag in one `Model` | Pick an unused tag |
| `Unexpected 'dict' key type '` | A `dict` key that is not `str` | Key by `str` |
| `type object '` … `' has no attribute '` | Generated name guessed from the class, not the method | `<Type>.<MethodPascalCase>Request/Response` |
| `NameError: name '` … `' is not defined` in a `*_rbt.py` | A `Model` shared across API packages | Per-package subclasses (Limits) |

## See also

- [`api-methods.md`](api-methods.md) — factories, options, servicer signatures
- [`state-scalar-fields.md`](state-scalar-fields.md) — scalar zero values, constructor-set values
- [`api-schema-evolution.md`](api-schema-evolution.md) — changing a persisted API
