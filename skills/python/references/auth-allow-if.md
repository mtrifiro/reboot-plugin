---
title: Compose Predicates with `allow_if(all=...)` / `allow_if(any=...)`
impact: HIGH
impactDescription: All non-trivial authorization is composed from `allow_if` and predicates
tags: auth, allow_if, predicate, all, any, composition
summary: "`is_app_internal` in `any` turns anonymous `Unauthenticated` into `PermissionDenied`; `allow_if(all=[...])` or `allow_if(any=[...])`, never both or nested; `all` short-circuits."
step: auth
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: ""
---

# Compose Predicates with `allow_if(all=...)` / `allow_if(any=...)`

## When you are here

Combining predicates into one rule. Shipped predicates:
`auth-built-in-predicates.md`; your own: `auth-custom-predicates.md`;
per-method rules: `servicer-authorizer.md`.

## Do this

Pass exactly one keyword: `all=[...]` (every predicate `Ok`) or `any=[...]`
(at least one `Ok`).

```python
from reboot.aio.auth.authorizers import (
    allow_if, has_verified_token, is_app_internal, state_id_is_user_id,
)


def authorizer(self):
    # Authenticated AND an app condition; cheap check first.
    return allow_if(all=[has_verified_token, my_predicate])


def authorizer(self):
    # The owner, OR any in-app call (initialize, scheduled work, servicers).
    return allow_if(any=[state_id_is_user_id, is_app_internal])
```

Evaluation (1.6.0 `AllowIfAuthorizerRule`):

- Predicates run **one at a time, in list order**, never concurrently — for
  `all` and `any` alike.
- `all` returns the first `Unauthenticated` / `PermissionDenied`; later
  predicates may assume earlier ones returned `Ok` (put one reading
  `context.auth.user_id` after `has_verified_token`). Cheap,
  identity-establishing predicates first.
- `any` returns the first `Ok`; else `PermissionDenied` if any predicate
  returned it, otherwise `Unauthenticated`. Clients use this to choose
  "sign in" vs "forbidden".

`context.app_internal` is true in every nested call (other servicer,
`initialize`, scheduled work, the framework's `User.set_claims`), so
`any=[is_app_internal, <user predicate>]` fits a type other actors call.
The stdlib `OrderedMapServicer` defaults to `allow_if(all=[is_app_internal])`.

## Never

- `allow_if(all=[...], any=[...])` — asserts
  ``Exactly one of `all` or `any` must be passed``.
- `allow_if(any=[is_app_internal, allow_if(all=[a, b])])` — rules do not
  nest (an `AuthorizerRule` is not a predicate; `mypy` rejects it). Write
  one predicate combining `a` and `b` (`auth-custom-predicates.md`).
- Read a `PermissionDenied` from `allow_if(any=[is_app_internal,
  has_verified_token])` as "signed in but forbidden". `is_app_internal`
  returns `PermissionDenied` to every external caller, so anonymous callers
  never get `Unauthenticated` and never learn to sign in. When it matters,
  use one predicate:

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
  `has_verified_token` in `all=[...]` — it runs for unauthenticated callers.

## Limits

- One level of composition per `allow_if`; anything more is a custom predicate.

## Scales as

- Each predicate that reads another actor adds one reader call per
  authorized call; only short-circuiting skips it.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| ``Exactly one of `all` or `any` must be passed`` | Both or neither keyword given | Pass one of `all=` / `any=` |

## See also

- [`auth-built-in-predicates.md`](auth-built-in-predicates.md) — the three shipped predicates
- [`auth-custom-predicates.md`](auth-custom-predicates.md) — combining checks in one predicate
- [`servicer-authorizer.md`](servicer-authorizer.md) — per-method rules, tokenless call paths
