---
title: OAuth Providers — Choosing a Production Provider
impact: HIGH
impactDescription: The provider you launch with fixes your user-ID namespace; switching providers later strands all user-keyed state, so choose deliberately before you have production users
tags: auth, oauth, development, anonymous, google, github, auth0, ory, provider, production, migration, claims, consent
summary: "Switching providers later strands user state; `OAuthProviderByEnvironment(dev=Development(), prod=Google(...))`, credentials as secrets, `/__/oauth/callback`."
step: auth
applies: [mcp-ui, web-app]
always: false
when-web-app: "you pick a real (production) provider"
verified: 1.6.0
docs: ""
---

# OAuth Providers — Choosing a Production Provider

## When you are here

You are filling `Application(oauth=...)` (the identity slot deciding
`context.auth.user_id` for MCP clients and browsers) or replacing
`Development()` before launch. Own provider: `auth-custom-oauth-provider.md`;
calling a provider's API as the user: `auth-store-tokens.md`,
`python/references/auth-external-api-calls.md`.

## Do this

`oauth=` takes a selector: `OAuthProviderByEnvironment(dev=..., prod=...)`
— fake sign-in locally, real provider elsewhere, one `main.py`:

```python
import os
from reboot.aio.auth.oauth_providers import (
    Development,
    Google,
    OAuthProviderByEnvironment,
)
from reboot.aio.auth.oauth import OAuth

async def main():
    await Application(
        servicers=[UserServicer, CounterServicer],
        oauth=OAuth(
            provider=OAuthProviderByEnvironment(
                dev=Development(),
                prod=Google(
                    client_id=os.environ.get("GOOGLE_OAUTH_CLIENT_ID"),
                    client_secret=os.environ.get(
                        "GOOGLE_OAUTH_CLIENT_SECRET"
                    ),
                ),
            ),
        ),
    ).run()
```

Providers (`reboot.aio.auth.oauth_providers`):

| Provider | Construction | Identity issued | Use |
| --- | --- | --- | --- |
| `Development()` | no args | stable `dev-{hash}` per fake identity, account-picker UI; reset on `rbt dev expunge` | local dev only |
| `Google(...)` | `client_id=, client_secret=` | the Google account's OIDC `sub` | users sign in with Google |
| `GitHub(...)` | `client_id=, client_secret=` | numeric account ID (as `str`) | users sign in with GitHub |
| `Auth0(...)` | `domain=, client_id=, client_secret=` | Auth0 OIDC `sub`, encoding the upstream connection (`google-oauth2\|…`, `auth0\|…`) | several login methods (Google, GitHub, password, SSO) behind one provider, or user management (profiles, password resets, MFA, blocking) |
| `Ory(...)` | `domain=, client_id=, client_secret=` | Ory OIDC `sub` (the Kratos identity id, default non-pairwise subjects) | users in an Ory Network project or self-hosted Ory |
| `Anonymous()` | no args | fresh `anon-{ULID}` per OAuth flow, no sign-in UI | throwaway builds only |

`Auth0` `domain=` is the tenant (`your-tenant.us.auth0.com`); login
methods are chosen in Auth0. `Ory` `domain=` is the project
(`your-slug.projects.oryapis.com`). Servicers and rules are
provider-agnostic; only `main.py` changes.

**Credentials are the user's job — tell them.** App registration, client
ID / secret and callback URL happen in the provider's console; nothing
works until they do:

- **Google**: [Setting up OAuth 2.0](https://support.google.com/cloud/answer/6158849) — an OAuth client ID of type "Web application".
- **GitHub**: [Creating an OAuth app](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/creating-an-oauth-app) (a **GitHub App** with expiring user tokens if you need refresh tokens).
- **Auth0**: a **Regular Web Application** in the [dashboard](https://auth0.com/docs/get-started/auth0-overview/create-applications); enable upstream connections on its Connections tab.
- **Ory**: an **OAuth2 client** in the [Ory Console](https://www.ory.sh/docs/oauth2-oidc/authorization-code-flow) with the authorization-code grant and `openid` (plus `email` / `profile` for requested claims, `offline_access` if used).

Redirect URI: `<your-app-base-url>/__/oauth/callback` (note `/__/`).
Under `rbt dev run` register **both**
`http://127.0.0.1:9991/__/oauth/callback` and
`http://localhost:9991/__/oauth/callback` (providers treat them as distinct).

Credentials go in env vars (any uppercase name; `REBOOT_*` / `RBT_*`
reserved): locally `export ...` or `--env=NAME=...`; Reboot Cloud
`rbt cloud secret set NAME`
(`python/references/lifecycle-reboot-cloud.md`,
`python/references/lifecycle-secrets.md`).

**Identity claims.** `claims=` (e.g. `Google(claims=["email"])`, or
`claims={"email": "verified-email"}` to rename) delivers verified claims
to `User.set_claims` on every sign-in; the provider requests the scopes
and rejects undeliverable claims at construction. Without `claims=`,
`set_claims` never runs; with them, override it as a full replace (the
generated default raises `NotImplementedError`) —
`python/references/auth-claims.md`.

`Ory` also takes `webhook_secret=` (requires `claims=`) for an Ory Action
calling `POST /__/oauth/ory/webhook` after the settings flow, so email
changes propagate before next sign-in (see the `Ory` docstring).

**Before launch:** sign in as a real user (provider page, not the picker);
check `context.auth.user_id` is the provider's ID, not `dev-{hash}`;
confirm `state_id_is_user_id` rules accept the owner and reject others.

## Never

- Switch providers once you have real users — no shared ID space, so
  every user ID changes, stranding `state_id=user_id` state (same human,
  fresh empty actor), `state_id_is_user_id` rules, `User`-typed actors,
  user-keyed indexes. No secure migration proves old-ID data belongs to
  a new account.
- Launch on `Anonymous()` "for now" — its IDs are unauthenticated
  throwaways, so "claim your data" later is guesswork or identity theft.
  Pick the real provider before any production state (even an internal
  pilot) and start clean.
- Ship `Development()` — real customers must never see the fake picker.
- Change which Auth0 connections you offer casually — it can change
  users' `sub`s.
- Hard-code the client ID / secret in `main.py`, commit them, or put
  them in `.rbtrc` (checked into git).
- `os.environ["..."]` for a `prod=`-only provider — the constructor runs
  under `rbt dev` too. Use `os.environ.get(...)`; the provider rejects an
  empty `client_id` / `client_secret` only when selected, so production
  still fails fast.
- Trust the client name on the consent screen — it is attacker-chosen;
  the `redirect_uri` host is the signal.
- Build profiles, password resets, or MFA yourself on `Google` /
  `GitHub` — use `Auth0`.

## Limits

- `dev` is selected only under `rbt dev run`; `prod` everywhere else
  (`rbt serve`, Reboot Cloud, unclassified). Both arms required; a
  selected `None` arm fails startup, even with nothing to auto-construct.
- No `oauth=` means no OAuth server; an app with a `User`-typed
  auto-construct servicer then fails to start. In unit tests omit it: the
  harness supplies a test provider;
  `await rbt.create_external_context_as(name, user_id)` impersonates.
- `oauth=` takes one provider; Google *and* GitHub needs design not
  covered here.
- `Development()` and `Anonymous()` issue no provider tokens.
- MCP clients register dynamically (`POST /__/oauth/register`, RFC 7591),
  so anyone can register a `redirect_uri` they control. Hence
  `/__/oauth/authorize` shows a consent screen (client name, prominently
  the `redirect_uri` host) and requires a CSRF-protected
  `POST /__/oauth/consent`; PKCE doesn't help (attacker holds the
  verifier). Automatic, unconfigurable; the user is the last defense.
  `token_verifier=` apps run no Reboot OAuth server.
- Ory: identity edits through Ory's admin API skip flow-scoped actions
  and propagate at the next sign-in; the webhook never creates a `User`.

## Scales as

- Not measured.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `No OAuth provider is configured for this environment.` | The selected arm is `None` | Put a provider in that arm |
| ``requires a non-empty `client_id`.`` | The selected provider's credential env var is unset | Set it (`rbt cloud secret set ...` in production) |

## See also

- [`auth-custom-oauth-provider.md`](auth-custom-oauth-provider.md) — when no provider fits
- [`auth-store-tokens.md`](auth-store-tokens.md) — calling the provider's API
- [`python/references/auth-claims.md`](../../python/references/auth-claims.md) — `set_claims` rules
