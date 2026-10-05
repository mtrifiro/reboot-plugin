---
title: Writing Your Own OAuth Provider
impact: MEDIUM
impactDescription: Only needed when no shipped provider fits; the contract is small but strict — an unstable user id silently fragments user state, and a wrong `state`/`redirect_uri` handling breaks the flow at runtime, not startup.
tags: auth, oauth, provider, custom, oidc, okta, keycloak, sso, identity, exchange-code, authorization-url, store_tokens
summary: "An unstable `exchange_code` user id strands users; subclass `RegisteredOAuthProvider`: `authorization_url`, `validate()`, `mount_routes()`, `token_service_id`."
step: auth
applies: [mcp-ui]
always: false
when: "none of the shipped OAuth providers fits"
verified: 1.6.0
docs: ""
---

# Writing Your Own OAuth Provider

## When you are here

No shipped provider fits `Application(oauth=...)`. Reach here **last**:

1. **`Google` / `GitHub`** for direct sign-in with those.
2. **`Auth0`** for several login methods or user management (brokers most
   IdPs, enterprise SSO included); **`Ory`** for Ory Network / self-hosted Ory.
3. **Custom** only for the rest: self-hosted Keycloak, internal SSO you
   can't front with Auth0, an OAuth service Auth0 can't broker.

Choosing shipped providers: `auth-oauth-providers.md`.

## Do this

Subclass **`RegisteredOAuthProvider`** (`reboot.aio.auth.oauth_providers`)
for an authorization-code IdP with a pre-registered `client_id` /
`client_secret`; it handles credentials, extra `scopes=`, `store_tokens=`,
and a fail-fast `validate()`. Subclass `OAuthProvider` only for
non-standard schemes (in-tree: `Development`, `Anonymous`).

**Copy the closest shipped provider's source** (installed `reboot`
package), changing only endpoint URLs, `_REQUIRED_SCOPE`, constructor
extras (base URL, realm, tenant), and `token_service_id`:

- **`Auth0`** — model for OIDC IdPs (Keycloak, Okta): user id from the ID
  token's `sub`, a constructor extra (`domain=`) checked in `validate()`,
  full `store_tokens=True` incl. `offline_access`.
- **`GitHub`** — model for plain OAuth (no ID token): user id from the
  IdP's user-info API with the new access token.
- **`Google`** — refresh-token knob in `authorization_url`
  (`access_type=offline`).

Implement two methods; Reboot's OAuth server does the rest (`/__/oauth/...`
endpoints, minting/verifying `state`, minting app access tokens, setting
`context.auth.user_id`):

- **`authorization_url(state, redirect_uri) -> str`** — IdP authorize URL
  with `client_id`, scopes, `response_type=code`, and **`state` and
  `redirect_uri` verbatim** (`state` is a JWT verified on callback for
  CSRF; `redirect_uri` is the server's `/__/oauth/callback`).
- **`exchange_code(code, redirect_uri) -> ExchangeResult`** — POST the
  code to the token endpoint (plain `aiohttp` / `httpx`); user id from the
  `id_token`'s `sub` or the user-info API. Raising is safe: the server
  logs it and redirects with `access_denied`.

**Identity claims** (optional): declare deliverable claims and each one's
scope in class-level `_AVAILABLE_CLAIMS`; pass `claims=` to
`super().__init__` (rejects unavailable claims, derives scopes); pass the
decoded ID token / userinfo through `self._presented_claims(...)` into
`ExchangeResult.claims` — it keeps only requested claims under their
presented names (protocol claims like `exp`, `nonce`, … never leak) and
returns `None` when none were requested. Claims reach `User.set_claims`
on every sign-in.

Optional hooks:

- **`validate()`** — raise `InputError` on bad config; called once when
  the provider is selected, so a misconfigured `prod=` arm fails at
  startup. Call `super().validate()` first (see `Auth0.validate`).
- **`mount_routes(http)`** — provider-specific routes, rarely needed
  (`Development`'s login page; `Ory`'s settings-flow webhook). A route
  delivering identity changes between sign-ins may call
  `self._set_claims_if_exists(...)` (wired via `use_set_claims_if_exists`
  before `mount_routes` runs; see `Ory._webhook`).

Wire it like a shipped provider, then **tell the user** to register the
client in the IdP console, get `client_id` / `client_secret`, and allow
`<base-url>/__/oauth/callback` as redirect URI — only they can:

```python
oauth=OAuth(
    provider=OAuthProviderByEnvironment(
        dev=Development(),
        prod=MyIdP(
            client_id=os.environ.get("MY_IDP_CLIENT_ID"),
            client_secret=os.environ.get("MY_IDP_CLIENT_SECRET"),
        ),
    ),
)
```

### Supporting `store_tokens=True`

1. Override **`token_service_id`** with the service's state ID (e.g.
   `"sso.example.com"`); apps call `OAuthTokenManager.ref(<that id>).fetch(...)`.
2. When `self._store_tokens` is set, return `ExchangeResult.tokens` as
   `OAuthTokens` (`rbt.std.oauth.v1.oauth_rbt`: `access_token`,
   `refresh_token`, `expires_at`, `scopes`); else `tokens=None`.
3. Add refresh-token knobs (`access_type=offline`, `offline_access`) in
   `authorization_url` only when `self._store_tokens` is set.

The server stores them encrypted and carries a prior `refresh_token`
forward (`auth-store-tokens.md`).

## Never

- Return an unstable user id from `exchange_code` — it becomes
  `context.auth.user_id`, the key of all user-keyed state. Use an OIDC
  `sub` or numeric account id, never a changeable email or anything
  session-scoped. It fixes the user-ID namespace
  (provider-permanence rule, `auth-oauth-providers.md`).
- Rewrite or re-mint `state` / `redirect_uri` in `authorization_url` —
  the server verifies both on callback.
- Return tokens when `store_tokens` is off — non-opted-in apps must never
  carry these secrets.
- Put claims from an unverified source in `ExchangeResult.claims` — only
  an ID token from the token endpoint, or the userinfo endpoint, over TLS.
- A claims-delivering route in `mount_routes` that doesn't authenticate
  its caller (a shared secret, a signature) — it decides who can impersonate
  users.
- Write the provider from a blank page — adapt `Auth0` / `GitHub`.

## Limits

- `_set_claims_if_exists` delivers only to a `User` that already exists;
  it never creates one (webhooks fire instance-wide).
- Deliveries may repeat (`set_claims` is a full replace, idempotent) and
  are last-write-wins: a delayed retry can briefly overwrite a newer
  change until the next delivery or sign-in.
- `oauth=` takes one provider; the selector picks one per environment.
- At 1.6.0, `store_tokens=True` fails at startup because the wheel lacks
  `reboot.std.oauth` (`auth-store-tokens.md` § Limits).

## Scales as

- Not measured.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `access_denied` | `exchange_code` raised; the server logged it and redirected | Read the server log for the exchange error |

## See also

- [`auth-oauth-providers.md`](auth-oauth-providers.md) — provider choice is permanent
- [`auth-store-tokens.md`](auth-store-tokens.md) — the token-capture machinery
- [`python/references/auth-claims.md`](../../python/references/auth-claims.md) — handling delivered claims
