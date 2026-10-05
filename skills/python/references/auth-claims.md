---
title: Identity Claims and `User.set_claims`
impact: MEDIUM
impactDescription: Without `claims=` the app sees only an opaque user ID and `set_claims` never runs; a wrong override signature or merge semantics breaks sign-in or keeps stale identity
tags: auth, claims, set_claims, User, oauth, Development, Google, email, name, identity
summary: "Request `claims=` on the provider and override `User.set_claims` with the right signature; replace, never merge, on each delivery; never key roles on `Development()` user IDs."
step: auth
applies: [mcp-ui, web-app]
always: false
when: "you use claims or `set_claims`"
verified: 1.6.0
docs: ""
---

# Identity Claims and `User.set_claims`

## When you are here

The app uses `Application(oauth=...)` and needs facts *about* the user
(email, name, verified-email flag), not just the opaque
`context.auth.user_id`. Claims are opt-in per provider and arrive in the
`User` type's framework-provided `set_claims` transaction. Choosing
providers: the front-door skill's OAuth section; rules:
`servicer-authorizer.md`.

## Do this

Request claims in **every** arm, including `Development()`:

```python
from reboot.aio.applications import Application
from reboot.aio.auth.oauth import OAuth
from reboot.aio.auth.oauth_providers import (
    Development,
    OAuthProviderByEnvironment,
)

application = Application(
    servicers=[UserServicer, ...],
    oauth=OAuth(
        provider=OAuthProviderByEnvironment(
            dev=Development(claims=["email", "name"]),
            prod=...,  # e.g. Google(<credentials>, claims=["email", "name"])
        ),
    ),
)
```

Override `set_claims` in the servicer for the type named `User`: a
`Transaction` (may call other actors, e.g. a role lookup), using
`self.state`, with no `state` parameter:

```python
from reboot.aio.contexts import TransactionContext


class UserServicer(User.Servicer):

    async def set_claims(
        self,
        context: TransactionContext,
        request: User.SetClaimsRequest,
    ) -> None:
        # Full replace: an absent claim is no longer asserted.
        self.state.email = request.claims.get("email", "")
        self.state.name = request.claims.get("name", "")
```

`request.claims` is a `dict[str, Any]` of the complete current requested
claims, keyed by claim name (or your mapping:
`claims={"email": "verified-email"}`). On every sign-in the framework
auto-constructs the `User` (idempotent), then calls `set_claims`;
re-delivery must be harmless.

Claims each provider can deliver (1.6.0 `_AVAILABLE_CLAIMS`):

| Provider | Claims |
| --- | --- |
| `Development` | `email`, `email_verified`, `name` (fabricated: `alice@example.com`, `Alice`, …) |
| `Google` | `email`, `email_verified`, `name`, `given_name`, `family_name`, `picture`, `locale`, `profile` |
| `GitHub` | `email`, `email_verified` |
| `Auth0` | `email`, `email_verified`, `name`, `given_name`, `family_name`, `middle_name`, `nickname`, `picture`, `updated_at` |
| `Ory` | `email`, `email_verified`, `name`, `given_name`, `family_name`, `username`, `website`, `updated_at` |
| `Anonymous` | none |

Registered providers request the needed OAuth scopes automatically.

## Never

- `Development()` with no `claims=` while expecting identity — the app
  sees only `dev-{hash}`, `set_claims` never runs, nothing warns.
- Override `set_claims(self, context, state, request)` — mypy:
  `Signature of "set_claims" incompatible with supertype`. Use
  `(self, context, request)` and `self.state`.
- Request claims without overriding `set_claims` — the generated
  default raises `NotImplementedError` at sign-in.
- Declare `set_claims` (or `create`) in the `User` API — both are
  reserved and injected; override in the servicer.
- Merge claims into existing state — each delivery is the whole truth.
- Key roles or a directory by `Development()` user IDs — opaque, per-app,
  changed by an expunge; only five identities (Alice, Ben, Carlos, Dani,
  Esi). Key by the `email` claim; look up the user ID at runtime.

## Limits

- Only the type named `User` gets `create` / `set_claims`; claims reach
  no other type directly.
- `set_claims` is app-internal only: generated middleware rejects external
  calls with `PermissionDenied` before any authorizer, so not even
  `allow()` exposes it (1.6.0 source). reboot-crm-01 saw it web-callable
  under the default `User` rule; on a runtime without that check, add
  `User.Authorizer(set_claims=allow_if(all=[is_app_internal]))`.
- Delivered per authorization-code exchange (sign-in), not on refresh;
  a refresh never clears claims. Access tokens last 24 h by default
  (`access_token_ttl_seconds=`).
- `Ory(webhook_secret=...)` (requires `claims=`) also delivers changes
  between sign-ins, but only to `User`s that already exist.
- An undeliverable claim name raises at construction, listing available
  ones; `Anonymous` rejects `claims=`.

## Scales as

- Sign-in waits on auto-construct and `set_claims`. Keep `set_claims`
  small: it holds an exclusive `User` lock, and a `User` locked by another
  transaction blocks sign-in (`servicer-transaction.md`, Limits).

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `Verified identity claims were delivered for this` | Provider sends claims; `UserServicer` doesn't override `set_claims` | Override it, or remove `claims=` |
| `cannot deliver the identity claim(s)` | Requested a claim the provider lacks | Pick from the listed available claims |
| `does not deliver identity claims; remove \`claims=\`` | `claims=` on a provider with none (`Anonymous`) | Remove it |
| `is a reserved method name for User types` | `set_claims` / `create` declared in the API | Delete the declaration; override in the servicer |
| `Signature of "set_claims" incompatible with supertype` | Override has a `state` parameter | `(self, context, request)` |

## See also

- [`servicer-authorizer.md`](servicer-authorizer.md) — rules, app-internal paths
- [`testing-harness.md`](testing-harness.md) — deliver claims in tests
- [`servicer-transaction.md`](servicer-transaction.md) — `set_claims` is a transaction
