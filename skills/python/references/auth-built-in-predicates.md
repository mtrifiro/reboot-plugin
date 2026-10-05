---
title: Built-In Authorizer Predicates
impact: HIGH
impactDescription: The three shipped predicates cover most auth needs without custom code
tags: auth, predicate, has_verified_token, is_app_internal, state_id_is_user_id
summary: "`has_verified_token`, `is_app_internal` and `state_id_is_user_id` and their common compositions; a self-scheduled workflow needs `is_app_internal`; predicates always take `**kwargs`."
step: auth
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: ""
---

# Built-In Authorizer Predicates

## When you are here

Choosing predicates for `allow_if(...)`. Composition: `auth-allow-if.md`;
your own: `auth-custom-predicates.md`.

## Do this

`reboot.aio.auth.authorizers` ships three; each takes keyword args and
returns `Ok`, `Unauthenticated`, or `PermissionDenied`. 1.6.0 bodies:

```python
def has_verified_token(*, context: ReaderContext, **kwargs):
    if context.auth is None:
        return Unauthenticated()
    return Ok()


def is_app_internal(*, context: ReaderContext, **kwargs):
    if context.app_internal:
        return Ok()
    return PermissionDenied()


def state_id_is_user_id(*, context: ReaderContext, **kwargs):
    if context.auth is None or context.auth.user_id is None:
        return Unauthenticated()
    if context.auth.user_id == context.state_id:
        return Ok()
    return PermissionDenied()
```

- **`has_verified_token`** — valid token; does **not** check the user is
  registered with the app. Baseline gate:
  `allow_if(all=[has_verified_token, can_access])`.
- **`is_app_internal`** — call from inside the app (servicer, `initialize`,
  scheduled work); external clients always get `PermissionDenied`. Gate for
  internal helpers; `OrderedMap` defaults to `allow_if(all=[is_app_internal])`.
- **`state_id_is_user_id`** — state ID equals caller's `user_id`, for actors
  that *are* a user. Implies `has_verified_token`.

```python
allow_if(all=[is_app_internal])                       # internal-only
allow_if(all=[has_verified_token])                    # any signed-in caller
allow_if(all=[state_id_is_user_id])                   # only the owner
allow_if(any=[state_id_is_user_id, is_app_internal])  # owner + background work
allow_if(any=[is_app_internal, has_verified_token])   # internal or signed in
```

### Self-scheduled workflows need `is_app_internal`

A workflow scheduled on the **same actor**
(`self.ref().schedule().<workflow>(context)`) runs app-internally with no
bearer token, even when a user's transaction scheduled it:

```python
# WRONG — owner-only. Called by alice, `place` schedules `pay`, which runs
# without a token: it gets `Unauthenticated` and `place` is aborted.
def authorizer(self):
    return allow_if(all=[state_id_is_user_id])

async def place(self, context: TransactionContext, request):
    await self.ref().schedule().pay(context)

# RIGHT — the owner OR an internal call.
def authorizer(self):
    return allow_if(any=[state_id_is_user_id, is_app_internal])
```

`any=[state_id_is_user_id, is_app_internal]` is the canonical rule for
user-owned actors with background work.

## Never

- `has_verified_token` or `state_id_is_user_id` alone on a servicer that
  other servicers call — a nested call carries **no** `context.auth`, so
  both return `Unauthenticated`. Add `is_app_internal` in `any=[...]`
  (`servicer-authorizer.md` § Never).
- Treat `has_verified_token` as "is a user of this app" — it only checks
  the token.
- A predicate signature without `**kwargs` — the runtime passes `context`,
  `state`, `request` by keyword and may add more.

## Limits

- `is_app_internal` never returns `Unauthenticated`; in `any=[...]` its
  `PermissionDenied` masks another's `Unauthenticated` (`auth-allow-if.md` § Never).
- `state_id_is_user_id` compares strings exactly; key actors by the
  provider-issued user ID.

## Scales as

- All three read only `context`; none makes a call.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `aborted with 'Unauthenticated': You are not authorized to call` | A token-based predicate saw no `context.auth`, often a scheduled or nested call | Add `is_app_internal` to an `any=[...]` |

## See also

- [`auth-allow-if.md`](auth-allow-if.md) — evaluation order and aggregation
- [`servicer-authorizer.md`](servicer-authorizer.md) — listing tokenless call paths
- [`auth-custom-predicates.md`](auth-custom-predicates.md) — predicates beyond these three
