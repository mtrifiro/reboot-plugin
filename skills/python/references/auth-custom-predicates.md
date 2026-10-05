---
title: Write Custom Authorizer Predicates
impact: MEDIUM
impactDescription: App-specific access rules require custom predicates; the shipped ones aren't enough alone
tags: auth, custom, predicate, allow_if, async, sync, per-method, Authorizer
summary: "Per-method rules via `<Type>.Authorizer(method=rule, _default=rule)`; keyword-only predicates ending in `**kwargs`, annotated or `mypy` fails; check `context.app_internal` first; `PermissionDenied` vs. `Unauthenticated`."
step: auth
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: "https://docs.reboot.dev/users/authorization"
---

# Write Custom Authorizer Predicates

## When you are here

The shipped predicates (`auth-built-in-predicates.md`) can't express a
rule — ownership stored in state, team membership, a role — or methods
of one type need different rules. Composition semantics are
`auth-allow-if.md`; when rules are required at all is
`servicer-authorizer.md`.

## Do this

Give each method its rule with the generated `<Type>.Authorizer(...)`,
and write each app-specific check as a keyword-only predicate:

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

- **Signature.** `(*, context, state, request, **kwargs)`, keyword-only.
  Declare only the arguments the body reads; `**kwargs` absorbs the rest
  and anything the runtime adds later. `context` is always a
  `ReaderContext`; `state` and `request` may be `None`.
- **`state`** is annotated with the **pydantic** `<X>State` from your
  API definition — that is what a pydantic app's predicate receives.
- **Check `context.app_internal` first** when the type is called from
  other servicers, `initialize`, or scheduled work: those calls carry
  no `context.auth`.
- **`Unauthenticated`** means "no identity — sign in";
  **`PermissionDenied`** means "identity, but not allowed". Clients
  choose between a login redirect and a 403 on it.
- **Sync or async.** `allow_if` awaits an `async def` predicate.
  Reading another actor goes through its declared `Reader`:

```python
async def is_team_member(*, context, state, **kwargs):
    response = await Team.ref(state.team_id).members(context)
    if context.auth.user_id in response.member_ids:
        return errors.Ok()
    return errors.PermissionDenied()

# Cheap identity check first; the RPC runs only for signed-in callers.
allow_if(all=[has_verified_token, is_team_member])
```

A predicate shared by several methods that does read `request` gets the
union of their request models: annotate `request: Any = None` (or the
union) and narrow with `isinstance` before reading a field only one
model has.

A predicate returns only `Ok`, `Unauthenticated`, or
`PermissionDenied` from `rbt.v1alpha1.errors_pb2`. The module also holds
the framework errors a typed error union widens to: `NotFound
AlreadyExists InvalidArgument FailedPrecondition OutOfRange
ResourceExhausted DeadlineExceeded Cancelled Unavailable Unimplemented
Internal Unknown DataLoss Aborted StateNotConstructed
StateAlreadyConstructed UnknownService UnknownTask InvalidMethod`.

## Never

- `def can_edit(context, state, request):` — positional and no
  `**kwargs`; the runtime calls by keyword. Use the keyword-only form.
- One predicate that tells methods apart by `isinstance(request, ...)`
  — a method declared `request=None`, or two methods sharing a request
  model, cannot get its own rule. Use `<Type>.Authorizer(method=...)`.
- A custom `Authorizer` subclass, or splitting state across servicers,
  to get per-method rules — `<Type>.Authorizer` already takes one rule
  per method.
- `allow_if(any=[is_app_internal, allow_if(all=[a, b])])` — rules don't
  nest; write one predicate that combines `a` and `b`.
- Annotate `state` with `<Type>Authorizer.StateType` / `.RequestTypes`
  — those alias the **protobuf** types (`<name>_pb2.TaskList`), not the
  pydantic model the predicate receives. They type-check (same field
  names) while naming the wrong class.
- Return `AuthorizerRule[TaskListState, Any]` from a helper — the
  generated `<Type>.Authorizer` expects `AuthorizerRule[<protobuf
  state>, <protobuf requests>]` and rejects it at the point of use. Use
  `AuthorizerRule[Any, Any]`, as above.
- `if request is None: <check auth>` without checking
  `context.app_internal` first — nested reader calls from other
  servicers are then denied with a confusing `Unauthenticated`.
- An expensive predicate before `has_verified_token` in `all=[...]`.

## Limits

- Unannotated predicates fail `mypy`: `allow_if` reports
  `Argument "any" ... has incompatible type "list[function]"`, and a
  helper returning a rule reports `Need type annotation`.
- The annotations only check anything if `mypy` resolves the API
  package: `mypy_path` must include the project-root `api/`, and the
  generated-code ignore must name `<pkg>.v1.<name>_rbt`, not
  `<pkg>.v1.*` — a blanket ignore makes `TaskListState` `Any`, and a
  misspelled field passes (`lifecycle-project-setup.md`).
- A method omitted from `<Type>.Authorizer(...)` gets `_default`; when
  `_default` is omitted too it is `allow_if(all=[is_app_internal])`, so
  a method added later is unreachable from outside until named.
- A predicate that fails closed on `state is None` turns a malformed
  state ID (e.g. a whole JSON row passed as the ID) into
  `PermissionDenied`; when every call is refused, check the ID before
  the rule (client-portal, 1.6.0).

## Scales as

- A predicate that reads another actor costs one reader RPC per
  authorized call, readers included (`servicer-authorizer.md` § Scales
  as). Prefer facts on the authorized actor's own `state`.

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
