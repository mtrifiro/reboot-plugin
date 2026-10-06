---
title: Write Custom Authorizer Predicates
impact: MEDIUM
impactDescription: App-specific access rules require custom predicates; the shipped ones aren't enough alone
tags: auth, custom, predicate, allow_if, async, sync, per-method, Authorizer
summary: "Predicates must be keyword-only with `**kwargs` and check `context.app_internal` first; per-method rules via `<Type>.Authorizer(method=rule, _default=rule)`."
step: auth
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: "https://docs.reboot.dev/users/authorization"
---

# Write Custom Authorizer Predicates

## When you are here

Shipped predicates (`auth-built-in-predicates.md`) can't express the rule
(ownership in state, team membership, a role), or one type's methods need
different rules. Composition: `auth-allow-if.md`; when rules are required:
`servicer-authorizer.md`.

## Do this

Per-method rules via generated `<Type>.Authorizer(...)`; each app check
is a keyword-only predicate:

```python
from typing import Any

import rbt.v1alpha1.errors_pb2 as errors
from reboot.aio.auth.authorizers import (
    Authorizer,
    AuthorizerRule,
    allow_if,
    has_verified_token,
    is_app_internal,
)
from reboot.aio.contexts import ReaderContext
from <pkg>.v1.<name> import TaskListState


def is_owner(
    *,
    context: ReaderContext,
    state: TaskListState | None = None,
    **kwargs: Any,
) -> Authorizer.Decision:
    if context.app_internal:
        return errors.Ok()            # nested calls carry no identity
    if context.auth is None or context.auth.user_id is None:
        return errors.Unauthenticated()
    if state is not None and state.owner_id == context.auth.user_id:
        return errors.Ok()
    return errors.PermissionDenied()  # fail closed, including state None


# A helper that returns a rule spells out `AuthorizerRule[Any, Any]`.
def owner_only() -> AuthorizerRule[Any, Any]:
    return allow_if(all=[is_owner])


class TaskListServicer(TaskList.Servicer):
    def authorizer(self):
        return TaskList.Authorizer(
            tasks=allow_if(all=[has_verified_token]),
            archive=allow_if(all=[is_app_internal]),
            _default=owner_only(),
        )
```

- **Signature.** `(*, context, state, request, **kwargs)`, keyword-only;
  declare only what the body reads, `**kwargs` absorbs the rest. `context`
  is always a `ReaderContext`; `state` and `request` may be `None`.
- **`state`** is annotated with the **pydantic** `<X>State` from your API.
- **Check `context.app_internal` first** when other servicers,
  `initialize`, or scheduled work call the type: they carry no `context.auth`.
- **`Unauthenticated`** = "no identity — sign in"; **`PermissionDenied`** =
  "identity, but not allowed" (login redirect vs 403).
- **Sync or async.** `allow_if` awaits an `async def` predicate; read
  another actor through its declared `Reader`:

```python
async def is_team_member(*, context, state, **kwargs):
    response = await Team.ref(state.team_id).members(context)
    if context.auth.user_id in response.member_ids:
        return errors.Ok()
    return errors.PermissionDenied()

# Cheap identity check first; the RPC runs only for signed-in callers.
allow_if(all=[has_verified_token, is_team_member])
```

**Roles** are the same shape: the roster's reader returns each member's
roles, and the predicate checks the one the method needs; give each
method its rule in `<Type>.Authorizer(...)` (front desk checks guests
in, housekeeping marks rooms clean).

A predicate shared by several methods that reads `request` gets the union
of their request models: annotate `request: Any = None` (or the union) and
narrow with `isinstance` before reading a model-specific field.

A predicate returns only `Ok`, `Unauthenticated`, or `PermissionDenied`
from `rbt.v1alpha1.errors_pb2`, which also holds the framework errors a
typed error union widens to: `NotFound
AlreadyExists InvalidArgument FailedPrecondition OutOfRange
ResourceExhausted DeadlineExceeded Cancelled Unavailable Unimplemented
Internal Unknown DataLoss Aborted StateNotConstructed
StateAlreadyConstructed UnknownService UnknownTask InvalidMethod`.

## Never

- `def can_edit(context, state, request):` — positional, no `**kwargs`;
  the runtime passes `context`, `state`, `request` by keyword and may
  add more.
- One predicate that tells methods apart by `isinstance(request, ...)`
  — a `request=None` method, or two sharing a request model, can't get
  its own rule. Use `<Type>.Authorizer(method=...)`.
- A custom `Authorizer` subclass, or splitting state across servicers,
  to get per-method rules — `<Type>.Authorizer` already does it.
- `allow_if(any=[is_app_internal, allow_if(all=[a, b])])` — rules don't
  nest (`auth-allow-if.md` § Never); write one predicate combining them.
- Annotate `state` with `<Type>Authorizer.StateType` / `.RequestTypes`
  — they alias the **protobuf** types (`<name>_pb2.TaskList`), not the
  pydantic model received; they type-check (same fields) but name the
  wrong class.
- Return `AuthorizerRule[TaskListState, Any]` from a helper — the
  generated `<Type>.Authorizer` expects
  `AuthorizerRule[<protobuf state>, <protobuf requests>]` and rejects it.
  Use `AuthorizerRule[Any, Any]`.
- `if request is None: <check auth>` without checking
  `context.app_internal` first — nested reader calls get a confusing
  `Unauthenticated`.

## Limits

- Unannotated predicates fail `mypy`: `allow_if` reports
  `Argument "any" ... has incompatible type "list[function]"`, and a
  helper returning a rule reports `Need type annotation`.
- Annotations check nothing unless `mypy` resolves the API package:
  `mypy_path` must include project-root `api/`, and the generated-code
  ignore must name `<pkg>.v1.<name>_rbt`, not `<pkg>.v1.*` (a blanket
  ignore makes `TaskListState` `Any`; misspelled fields pass)
  (`lifecycle-project-setup.md`).
- A method omitted from `<Type>.Authorizer(...)` gets `_default`, which
  itself defaults to `allow_if(all=[is_app_internal])`: a method added
  later is externally unreachable until named.
- Failing closed on `state is None` turns a malformed state ID (e.g. a
  whole JSON row passed as the ID) into `PermissionDenied`; when every
  call is refused, check the ID before the rule (client-portal, 1.6.0).

## Scales as

- Reading another actor costs one reader RPC per authorized call, readers
  included (`servicer-authorizer.md` § Scales as). Prefer the actor's own `state`.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `has incompatible type "list[function]"; expected "Sequence[AuthorizerCallable[...]]"` | Unannotated predicate under `mypy` | Annotate as in Do this |
| `Need type annotation` | A helper returning a rule has no return type | `-> AuthorizerRule[Any, Any]` |
| `aborted with 'Unauthenticated': You are not authorized to call` | A predicate demanded identity on a nested, tokenless call | Return `Ok` for `context.app_internal` first |

## See also

- [`servicer-authorizer.md`](servicer-authorizer.md) — per-method constructor, call paths
- [`auth-allow-if.md`](auth-allow-if.md) — evaluation order, aggregation
- [`auth-built-in-predicates.md`](auth-built-in-predicates.md) — the shipped predicates
