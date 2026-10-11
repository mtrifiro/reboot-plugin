---
title: Authorizers — When to Write Them, What They See
impact: HIGH
impactDescription: Rules that ignore app-internal call paths or assume identity crosses servicer calls fail minutes later, or silently compute as if nobody is signed in
tags: servicer, authorizer, allow, allow_if, auth, authorizers, production, oauth, token-verifier, is_app_internal, context.auth, per-method
summary: "Without real rules every external call is denied; identity doesn't cross servicer calls; tokenless paths; `oauth=` vs `token_verifier=`."
step: auth
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: "https://docs.reboot.dev/users/authorization"
---

# Authorizers — When to Write Them, What They See

## When you are here

Writing `def authorizer(self)`; its rule is evaluated against
`context.auth` before each call. Predicates: `auth-built-in-predicates.md`,
`auth-custom-predicates.md`; claims: `auth-claims.md`.

## Do this

### When to write it

| Identity source on `Application(...)` | Callers have identity | Rule |
| --- | --- | --- |
| `oauth=OAuth(provider=OAuthProviderByEnvironment(dev=Development(), prod=...))` (any OAuth provider) | **Always**: verified `context.auth.user_id` (`dev-{hash}` under `Development()`) | Real `allow_if(...)` rules **from day one**, every servicer |
| `token_verifier=<TokenVerifier>` | Once wired to an external IdP | May wait for the verifier, not past the first harness test |
| Neither | Never | Every identity rule fails |

`Development()` is a real OAuth provider (fake account picker), so
`has_verified_token` and `state_id_is_user_id` behave as in production.
One OAuth server serves browsers (`rbt_session` cookie) and MCP clients
(`Authorization: Bearer`), so day-one rules apply to **both**.

| Mode | Missing `authorizer()` |
| --- | --- |
| `rbt dev` | **Allowed**, warning `*** <Type>.<Method> IS MISSING AUTHORIZATION ***` at most once a minute |
| `Reboot()` test harness | **Denied** (`PermissionDenied`), as in production |
| `rbt serve` / Reboot Cloud | **Denied** (`PermissionDenied`) |
| Servicer for the `User` type | Always enforced (`state_id_is_user_id` or `is_app_internal`), **including in dev** |

- App-internal calls pass the missing-authorizer default in every mode.
- The dev warning is a TODO list; the harness denies.
- `User` servicers usually need no `authorizer()`: the default is
  production-worthy, and `self.ref().state_id` is the user's ID even
  when `context.auth` is `None`.

### Before writing a rule: list the tokenless call paths

Each fails on first run, not at startup. Any yes → add
`is_app_internal` via `any=[...]`:

1. Does `initialize` call this servicer? (`InitializeContext` is
   app-internal.)
2. Does anything `schedule()` a method on this actor, including itself?
3. Does another servicer call this one, from a reader, writer,
   transaction, workflow or nested constructor?

### Shape

```python
from reboot.aio.auth.authorizers import (
    allow_if, has_verified_token, is_app_internal, state_id_is_user_id,
)
from reboot.aio.contexts import ReaderContext


class CounterServicer(Counter.Servicer):

    def authorizer(self):
        # Rule per method; unlisted methods use `_default`.
        return Counter.Authorizer(
            value=allow_if(any=[has_verified_token, is_app_internal]),
            reset=allow_if(all=[is_app_internal]),
            _default=allow_if(any=[state_id_is_user_id, is_app_internal]),
        )

    async def value(
        self, context: ReaderContext,
    ) -> Counter.ValueResponse:
        return Counter.ValueResponse(value=self.state.value)
```

- Every type has `<Type>.Authorizer(<method>=rule, ..., _default=rule)`
  (snake or Camel method names); `grep -n "class .*Authorizer("
  api/<pkg>/v1/<name>_rbt.py` shows the parameters.
- A bare rule returned from `authorizer()` becomes
  `<Type>.Authorizer(_default=rule)` (every method).
- Omitted `_default` is `allow_if(all=[is_app_internal])` (for `User`:
  `state_id_is_user_id` or `is_app_internal`), so a later-added method
  is internal-only until named.

## Never

- Omitting `authorizer()` "until later" — the test harness, `rbt serve`
  and Reboot Cloud deny every external call to it.
- `allow()` as a "safe default" — it makes the method public and
  unauthenticated (`auth-allow-deny.md`).
- Assume the caller's identity reaches an actor your servicer calls. A
  call from inside any servicer is app-internal with **no** bearer
  token; `context.auth` is `None` there (1.6.0 source: the generated
  stub deliberately does not forward the token). A rule of only
  `has_verified_token` / `state_id_is_user_id` denies it
  (`Unauthenticated`); anything derived from `context.auth` (a "mine"
  flag, per-user count, owner stamp, audit entry) silently computes as
  if nobody is signed in. Pass the user ID as a request field; trust it
  only when `context.auth is None and context.app_internal`, otherwise
  use `context.auth.user_id`.
- Gate per-method rules by `isinstance(request, ...)` in one predicate
  (`auth-custom-predicates.md` § Never).
- A predicate on type X that calls a reader on the actor it guards:
  the actor waits on itself. Read the `state` argument (crm-kit, 1.6.0).
- A client- or MCP-facing method that fans out and relies on the gates
  of what it reads: its nested calls arrive app-internal and pass every
  `is_app_internal` arm. Authorize the caller in that method first
  (crm-kit, 1.6.0).
- Read `PermissionDenied` from `allow_if(any=[has_verified_token,
  is_app_internal])` as "signed in but forbidden" — anonymous callers
  get it too (`auth-allow-if.md` § Never).

## Limits

- One `authorizer()` per servicer; per-method rules go in
  `<Type>.Authorizer(...)`.
- The authorizer runs in its own `ReaderContext` before the method
  body, with the actor's `state` (except for constructors) and the
  typed `request`.
- `User.set_claims` is app-internal only, checked before any
  authorizer; no rule (not even `allow()`) exposes it (`auth-claims.md`).

## Scales as

- A predicate that reads another actor (e.g. roles via
  `User.ref(user_id).profile(context)`) costs one reader RPC per
  authorized call, readers included; it doubled a page's round trips
  (student-system-07, 1.5.0). Prefer facts on the authorized actor's
  own `state`, or claims on `User` when only `User` methods need them.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `aborted with 'PermissionDenied': You are not authorized to call` | No rule allowed the caller (or a `deny()` matched); in harness/prod often a servicer with no `authorizer()` | Write a real `allow_if(...)` rule; add `is_app_internal` for internal paths |
| `aborted with 'Unauthenticated': You are not authorized to call` | A rule needed identity and the call had none, typically servicer-to-servicer | Add `is_app_internal`; pass identity in the request |
| `IS MISSING AUTHORIZATION` | `rbt dev` allowed a call to a servicer with no `authorizer()` | Write the rule before testing |

## See also

- [`auth-built-in-predicates.md`](auth-built-in-predicates.md) — what each predicate checks
- [`auth-custom-predicates.md`](auth-custom-predicates.md) — writing your own predicates
- [`testing-harness.md`](testing-harness.md) — app-internal and impersonated test contexts
