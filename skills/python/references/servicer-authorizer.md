---
title: Authorizers — When to Write Them, What They See
impact: HIGH
impactDescription: Rules that ignore app-internal call paths or assume identity crosses servicer calls fail minutes later, or silently compute as if nobody is signed in
tags: servicer, authorizer, allow, allow_if, auth, authorizers, production, oauth, token-verifier, is_app_internal, context.auth, per-method
summary: "Write real rules on every servicer before the first test; list the tokenless call paths first; identity does not cross servicer calls; `oauth=` vs. the `token_verifier=` escape hatch."
step: auth
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: "https://docs.reboot.dev/users/authorization"
---

# Authorizers — When to Write Them, What They See

## When you are here

You are deciding whether a servicer needs `def authorizer(self)` yet,
and writing it. Reboot evaluates the returned rule against
`context.auth` before each method call. Predicate details live in
`auth-built-in-predicates.md` / `auth-custom-predicates.md`; `allow()`
misuse in `auth-allow-deny.md`; identity claims in `auth-claims.md`.

## Do this

### When to write it

Identity comes from `Application(...)`:

| Identity source on `Application(...)` | When callers have identity | Rule |
| --- | --- | --- |
| `oauth=OAuth(provider=OAuthProviderByEnvironment(dev=Development(), prod=...))` (any OAuth provider) | **Always**: every caller gets a verified `context.auth.user_id` (`dev-{hash}` under `Development()`) | Write real `allow_if(...)` rules **from day one**, on every servicer |
| `token_verifier=<TokenVerifier>` | Only once the verifier is wired to an external IdP | Rules may wait for the verifier, but not past the first harness test |
| Neither | Never | Every identity rule fails |

`Development()` is a real OAuth provider: a fake account-picker
sign-in that mints a stable `dev-{hash}` per identity, so
`has_verified_token` and `state_id_is_user_id` behave as in
production. One OAuth server serves browsers (`rbt_session` cookie)
and MCP clients (`Authorization: Bearer`), so day-one rules are the
default for **both** MCP UIs and web apps.

Without `authorizer()`:

| Mode | Missing `authorizer()` |
| --- | --- |
| `rbt dev` | **Allowed**, with a `*** <Type>.<Method> IS MISSING AUTHORIZATION ***` warning at most once a minute |
| `Reboot()` test harness | **Denied** (`PermissionDenied`), as in production |
| `rbt serve` / Reboot Cloud | **Denied** (`PermissionDenied`) |
| Servicer for the `User` type | Always enforced (`state_id_is_user_id` or `is_app_internal`), **including in dev** |

App-internal calls pass the missing-authorizer default in every mode.
Because the harness denies, "defer until the verifier is wired" ends at
the first test, and the dev warning is only a TODO list. `User`
servicers usually need no `authorizer()`: the default is
production-worthy, and inside one `self.ref().state_id` is the user's
ID even when `context.auth` is `None`.

### Before writing a rule: list the tokenless call paths

None of these fail at startup; each fails the first time it runs. If
any answer is yes, the rule needs `is_app_internal` in an
`any=[...]`:

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

Every generated type has `<Type>.Authorizer(<method>=rule, ...,
_default=rule)` (snake or Camel method names). A bare rule returned
from `authorizer()` is wrapped as `<Type>.Authorizer(_default=rule)`
and applies to every method. If you omit `_default`, it is
`allow_if(all=[is_app_internal])` (for `User`:
`state_id_is_user_id` or `is_app_internal`), so a method added later
is internal-only until named. `grep -n "class .*Authorizer("
api/<pkg>/v1/<name>_rbt.py` shows the parameters.

## Never

- `return allow` — returns the function, not a rule. `return allow()`.
- `allow()` as a "safe default" — it declares the method public and
  unauthenticated (`auth-allow-deny.md`).
- Assume the caller's identity reaches an actor your servicer calls.
  A call from inside any servicer is app-internal and carries **no**
  bearer token: inside it `context.auth` is `None` (1.6.0 source: the
  generated stub deliberately does not forward the caller's token).
  A rule of only `has_verified_token` / `state_id_is_user_id` denies
  the call (`Unauthenticated`); anything derived from `context.auth`
  (a "mine" flag, per-user count, owner stamp, audit entry) silently
  computes as if nobody is signed in. Pass the user ID as a request
  field, and trust it only when `context.auth is None and
  context.app_internal`; otherwise use `context.auth.user_id`.
- Gate per-method rules by `isinstance(request, ...)` in one predicate
  — methods declared `request=None`, or sharing a request model,
  cannot get their own rule. Use `<Type>.Authorizer(method=...)`.
- Omit `authorizer()` on an `oauth=` app "until later" — the harness
  denies every external call to it.
- Treat a `PermissionDenied` from `allow_if(any=[has_verified_token,
  is_app_internal])` as "signed in but forbidden" — an anonymous caller
  also gets `PermissionDenied`, because `is_app_internal`'s denial wins
  the aggregation (`auth-allow-if.md`).

## Limits

- One `authorizer()` per servicer; per-method differentiation is the
  `<Type>.Authorizer(...)` constructor, not separate servicers.
- The authorizer runs in its own `ReaderContext` before the method
  body; it receives the actor's `state` (except for constructors) and
  the typed `request`.
- `User.set_claims` is app-internal only, checked before any
  authorizer, so no rule (not even `allow()`) exposes it
  (`auth-claims.md`).

## Scales as

- A predicate that reads another actor (e.g. roles on `User` via
  `User.ref(user_id).profile(context)`) costs one reader RPC per
  authorized call, readers included; it doubled a page's round trips
  (student-system-07, 1.5.0). Prefer facts on the authorized actor's
  own `state` (the rule receives it), or claims stored on `User` when
  only `User` methods need them.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `aborted with 'PermissionDenied': You are not authorized to call` | No rule allowed the caller; in the harness/prod, often a servicer with no `authorizer()` | Write the rule; add `is_app_internal` for internal paths |
| `aborted with 'Unauthenticated': You are not authorized to call` | A rule needed identity and the call carried none, typically a servicer-to-servicer call | Add `is_app_internal` to the rule; pass identity in the request |
| `IS MISSING AUTHORIZATION` | `rbt dev` allowed a call to a servicer with no `authorizer()` | Write the rule before testing |

## See also

- [`auth-built-in-predicates.md`](auth-built-in-predicates.md) — what each predicate checks
- [`auth-custom-predicates.md`](auth-custom-predicates.md) — writing your own predicates
- [`testing-harness.md`](testing-harness.md) — app-internal and impersonated test contexts
