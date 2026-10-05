---
title: OAuth Providers — Choosing a Production Provider
impact: HIGH
impactDescription: The provider you launch with fixes your user-ID namespace; switching providers later strands all user-keyed state, so choose deliberately before you have production users
tags: auth, oauth, development, anonymous, google, github, auth0, ory, provider, production, migration, claims, consent
summary: "The launch provider fixes the user-ID namespace, so switching later strands user state; `OAuthProviderByEnvironment(dev=Development(), prod=Google(...))`, credentials as secrets, the `/__/oauth/callback` URL."
step: auth
applies: [mcp-ui, web-app]
always: false
when-web-app: "you pick a real (production) provider"
verified: 1.6.0
docs: ""
---

# OAuth Providers — Choosing a Production Provider

## When you are here

You are filling `Application(oauth=...)` — the app's identity slot,
which decides who `context.auth.user_id` says the caller is, for MCP
clients and browsers alike — or replacing `Development()` before
launch. Writing your own provider is `auth-custom-oauth-provider.md`;
calling a provider's API as the user is `auth-store-tokens.md` and
`python/references/auth-external-api-calls.md`.

## Do this

`oauth=` takes a selector, not a provider:
`OAuthProviderByEnvironment(dev=..., prod=...)`. Keep the fake sign-in
locally and the real provider everywhere else — one `main.py`:

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

`Auth0`'s `domain=` is the tenant (`your-tenant.us.auth0.com`); the
choice of login method happens in Auth0, not your code. `Ory`'s `domain=`
is the project (`your-slug.projects.oryapis.com`). Servicers and
authorizer rules are provider-agnostic: only `main.py` changes.

**Credentials are the user's job — tell them.** Registering the app,
getting the client ID / secret, and authorizing the callback URL happen
in the provider's console; nothing works until they do it:

- **Google**: [Setting up OAuth 2.0](https://support.google.com/cloud/answer/6158849) — an OAuth client ID of type "Web application".
- **GitHub**: [Creating an OAuth app](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/creating-an-oauth-app) (a **GitHub App** with expiring user tokens if you need refresh tokens).
- **Auth0**: a **Regular Web Application** in the [dashboard](https://auth0.com/docs/get-started/auth0-overview/create-applications); enable upstream connections on its Connections tab.
- **Ory**: an **OAuth2 client** in the [Ory Console](https://www.ory.sh/docs/oauth2-oidc/authorization-code-flow) with the authorization-code grant and `openid` (plus `email` / `profile` for requested claims, `offline_access` if used).

Register `<your-app-base-url>/__/oauth/callback` (note `/__/`) as the
redirect URI. Locally under `rbt dev run` register **both**
`http://127.0.0.1:9991/__/oauth/callback` and
`http://localhost:9991/__/oauth/callback` — providers often treat them as
distinct.

Deliver credentials as environment variables (any uppercase name;
`REBOOT_*` and `RBT_*` are reserved): locally `export ...` or
`--env=NAME=...`; on Reboot Cloud `rbt cloud secret set NAME`
(`python/references/lifecycle-reboot-cloud.md`,
`python/references/lifecycle-secrets.md`).

**Identity claims.** `claims=` at construction (e.g.
`Google(claims=["email"])`, or a rename mapping
`claims={"email": "verified-email"}`) delivers verified claims to the
`User` type's `set_claims` on every sign-in; the provider requests the
scopes they need and rejects, at construction, any claim it cannot
deliver. Without `claims=`, `set_claims` is never called. With them,
override it (the generated default raises `NotImplementedError`; it is
callable only app-internally) as a full replace — a claim missing from
the request is no longer asserted (`python/references/auth-claims.md`):

```python
class UserServicer(User.Servicer):
    async def set_claims(
        self,
        context: TransactionContext,
        request: User.SetClaimsRequest,
    ) -> None:
        self.state.email = request.claims.get("email", "")
```

`Ory` also takes `webhook_secret=` (requires `claims=`) for an Ory Action
calling `POST /__/oauth/ory/webhook` after the settings flow, so an email
change propagates before the next sign-in (the `Ory` docstring shows the
configuration).

**Before launch:** sign in as a real user (the provider's page, not the
account picker); check `context.auth.user_id` is the provider's ID, not
`dev-{hash}`; confirm `state_id_is_user_id` rules accept the owner and
reject others.

## Never

- Switch providers once you have real users — providers share no ID
  space, so every user's ID changes and everything keyed on it is
  stranded: state created with `state_id=user_id` (the same human lands
  on a fresh, empty actor), `state_id_is_user_id` rules (now guarding a
  different set of identities), `User`-typed actors, user-keyed index
  actors. No reliable, secure migration proves old-ID data belongs to a
  new account.
- Launch on `Anonymous()` "for now" — its IDs look durable but are
  unauthenticated throwaways, so a later "claim your data" flow is
  guesswork or identity theft. Build on `Development()` (or
  `Anonymous()`), then pick the real provider before any production
  state — even an internal pilot — and start clean.
- Ship `Development()` — real customers must never see the fake picker.
- Change which Auth0 connections you offer casually — it can change
  users' `sub`s.
- Hard-code the client ID / secret in `main.py`, commit them, or put
  them in `.rbtrc` (checked into git).
- `os.environ["..."]` for a `prod=`-only provider — the constructor runs
  under `rbt dev` too. `os.environ.get(...)` returns `None` there, and
  the provider rejects an empty `client_id` / `client_secret` only when
  selected, so production still fails fast.
- Trust the client name on the consent screen — it is attacker-chosen;
  the `redirect_uri` host is the signal.
- Build profiles, password resets, or MFA yourself on `Google` /
  `GitHub` — use `Auth0`.

## Limits

- `dev` is selected only under `rbt dev run`; `prod` everywhere else —
  `rbt serve`, Reboot Cloud, any unclassified environment. Both arms are
  required; a selected arm of `None` fails startup, even for an app with
  nothing to auto-construct.
- Omitting `oauth=` means no OAuth server; an app with a `User`-typed
  auto-construct servicer then fails to start. In unit tests omit it:
  the harness supplies a test provider, and
  `await rbt.create_external_context_as(name, user_id)` impersonates a
  user.
- `oauth=` takes one provider; Google *and* GitHub needs deliberate
  design not covered here.
- `Development()` and `Anonymous()` issue no provider tokens.
- MCP clients register dynamically (`POST /__/oauth/register`, RFC 7591),
  so anyone can register a client with a `redirect_uri` they control.
  `/__/oauth/authorize` therefore shows a consent screen (client name,
  prominently the `redirect_uri` host) and requires a CSRF-protected
  `POST /__/oauth/consent`; PKCE doesn't help, the attacker holds the
  verifier. Automatic, unconfigurable, and the user is the last line of
  defense. Apps on `token_verifier=` run no Reboot OAuth server and see
  none of this.
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
