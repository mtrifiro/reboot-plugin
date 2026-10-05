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

You are choosing predicates for an `allow_if(...)` rule and want to know
exactly what each shipped one checks. Composition semantics are
`auth-allow-if.md`; writing your own is `auth-custom-predicates.md`.

## Do this

`reboot.aio.auth.authorizers` ships three predicates. Each takes keyword
args and returns `Ok`, `Unauthenticated`, or `PermissionDenied`. Their
1.6.0 bodies:

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

- **`has_verified_token`** — the caller presented a valid token. It
  does **not** check that the token's user is registered with the app.
  A baseline gate: `allow_if(all=[has_verified_token, can_access])`.
- **`is_app_internal`** — the call comes from inside the same app
  (another servicer, `initialize`, scheduled work). External clients
  always get `PermissionDenied`. The gate for stdlib-style internal
  helpers; the `OrderedMap` servicer defaults to
  `allow_if(all=[is_app_internal])`.
- **`state_id_is_user_id`** — the actor's state ID equals the caller's
  `user_id`. For actors that *are* a user (state IDs are user IDs).
  Implies `has_verified_token`.

Common compositions:

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
bearer token, even when the scheduling transaction was the user's:

```python
# WRONG — the owner-only rule denies the framework's scheduled call.
def authorizer(self):
    return allow_if(all=[state_id_is_user_id])

async def place(self, context: TransactionContext, request):
    # Called by alice, but `pay` runs app-internally, without a token:
    # its auth check returns `Unauthenticated` and `place` is aborted.
    await self.ref().schedule().pay(context)

# RIGHT — the owner OR an internal call.
def authorizer(self):
    return allow_if(any=[state_id_is_user_id, is_app_internal])
```

`any=[state_id_is_user_id, is_app_internal]` is the canonical rule for
user-owned actors with background work.

## Never

- `has_verified_token` or `state_id_is_user_id` alone on a servicer that
  other servicers call — a nested call carries **no** `context.auth`
  (the caller's identity does not travel with it), so both deny it with
  `Unauthenticated`. Add `is_app_internal` in an `any=[...]`
  (`servicer-authorizer.md` § Never).
- Treat `has_verified_token` as "is a user of this app" — it only
  checks the token.
- A predicate signature without `**kwargs` — the runtime passes
  `context`, `state`, and `request` by keyword and may add more; the
  shipped predicates all end in `**kwargs`. Mirror it.

## Limits

- `is_app_internal` never returns `Unauthenticated`; in an `any=[...]`
  its `PermissionDenied` masks another predicate's `Unauthenticated`
  (`auth-allow-if.md` § Never).
- `state_id_is_user_id` compares strings exactly; it needs actors keyed
  by the provider-issued user ID.

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
