---
title: Compose Predicates with `allow_if(all=...)` / `allow_if(any=...)`
impact: HIGH
impactDescription: All non-trivial authorization is composed from `allow_if` and predicates
tags: auth, allow_if, predicate, all, any, composition
summary: "`allow_if(all=[...])` or `allow_if(any=[...])`, never both, never nested; `all` short-circuits in order; `is_app_internal` in `any` turns anonymous callers' `Unauthenticated` into `PermissionDenied`."
step: auth
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: ""
---

# Compose Predicates with `allow_if(all=...)` / `allow_if(any=...)`

## When you are here

You are combining predicates into one authorizer rule. What each shipped
predicate checks is `auth-built-in-predicates.md`; writing your own is
`auth-custom-predicates.md`; per-method rules are `servicer-authorizer.md`.

## Do this

`allow_if` composes a list of predicate callables into a rule. Pass
exactly one keyword: `all=[...]` (every predicate must return `Ok`) or
`any=[...]` (at least one must).

```python
from reboot.aio.auth.authorizers import (
    allow_if, has_verified_token, is_app_internal, state_id_is_user_id,
)


def authorizer(self):
    # Authenticated AND some app-specific condition; cheap check first.
    return allow_if(all=[has_verified_token, my_predicate])


def authorizer(self):
    # The owner, OR any call from inside the app (initialize,
    # scheduled work, other servicers).
    return allow_if(any=[state_id_is_user_id, is_app_internal])
```

How the rule evaluates (1.6.0 `AllowIfAuthorizerRule`):

- Predicates run **one at a time, in list order** — never concurrently.
- `all` returns the first `Unauthenticated` or `PermissionDenied`; a
  later predicate may assume every earlier one returned `Ok` (so one that
  reads `context.auth.user_id` goes after `has_verified_token`). List
  cheap, identity-establishing predicates first.
- `any` returns the first `Ok`. If none, the result is
  `PermissionDenied` when any predicate returned `PermissionDenied`,
  otherwise `Unauthenticated`. Clients use the difference to choose
  "sign in" versus "forbidden".

`context.app_internal` is true inside every nested call — a call from
another servicer, from `initialize`, from scheduled work, and the
framework's own `User.set_claims` — so `any=[is_app_internal, <user
predicate>]` is the shape for a type other actors call into. The
stdlib does the same: `OrderedMapServicer` defaults to
`allow_if(all=[is_app_internal])`.

## Never

- `allow_if(all=[...], any=[...])` — asserts at runtime with
  ``Exactly one of `all` or `any` must be passed``. Pick one.
- `allow_if(any=[is_app_internal, allow_if(all=[a, b])])` — rules do not
  nest: an `AuthorizerRule` is not a predicate callable, so `mypy`
  rejects it. Write one predicate that combines `a` and `b`
  (`auth-custom-predicates.md`) and list that.
- Read a `PermissionDenied` from `allow_if(any=[is_app_internal,
  has_verified_token])` as "signed in but forbidden". `is_app_internal`
  returns `PermissionDenied` to every external caller, so an anonymous
  caller gets `PermissionDenied`, not `Unauthenticated`, and a client
  never learns to sign in. When the distinction matters, use one
  predicate:

  ```python
  import rbt.v1alpha1.errors_pb2 as errors


  def internal_or_signed_in(*, context, **kwargs):
      if context.app_internal:
          return errors.Ok()
      if context.auth is None:
          return errors.Unauthenticated()
      return errors.Ok()
  ```

- An expensive predicate (one that reads another actor) before
  `has_verified_token` in `all=[...]` — it runs for unauthenticated
  callers too.

## Limits

- One rule per `allow_if`; one level of composition. Anything more
  complex is a custom predicate.
- The order guarantee is for `all` and `any` alike: no predicate runs
  until the previous one has returned.

## Scales as

- Each predicate that reads another actor adds one reader call per
  authorized call; short-circuiting is the only way to skip it.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| ``Exactly one of `all` or `any` must be passed`` | Both or neither keyword given | Pass one of `all=` / `any=` |
| `aborted with 'PermissionDenied': You are not authorized to call` | No predicate allowed the call; with `is_app_internal` in `any`, also an anonymous caller | Check identity first, or use a combined predicate |

## See also

- [`auth-built-in-predicates.md`](auth-built-in-predicates.md) — the three shipped predicates
- [`auth-custom-predicates.md`](auth-custom-predicates.md) — combining checks in one predicate
- [`servicer-authorizer.md`](servicer-authorizer.md) — per-method rules, tokenless call paths
