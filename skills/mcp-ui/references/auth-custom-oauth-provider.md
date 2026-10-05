---
title: Writing Your Own OAuth Provider
impact: MEDIUM
impactDescription: Only needed when no shipped provider fits; the contract is small but strict — an unstable user id silently fragments user state, and a wrong `state`/`redirect_uri` handling breaks the flow at runtime, not startup.
tags: auth, oauth, provider, custom, oidc, okta, keycloak, sso, identity, exchange-code, authorization-url, store_tokens
summary: "Subclass `RegisteredOAuthProvider`: `authorization_url`, `exchange_code` returning a stable user id (it becomes `context.auth.user_id`), `validate()` / `mount_routes()`, and `token_service_id` for `store_tokens=True`."
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

1. **`Google` / `GitHub`** when users sign in with one of those directly.
2. **`Auth0`** for several login methods behind one provider or user
   management beyond a bare user id (it brokers most IdPs, enterprise
   SSO included); **`Ory`** when users live in an Ory Network project or
   self-hosted Ory.
3. **A custom provider** only for what none of those cover: a
   self-hosted Keycloak, an internal SSO you can't put Auth0 in front
   of, an OAuth service Auth0 can't broker.

Choosing among shipped providers is `auth-oauth-providers.md`.

## Do this

Subclass **`RegisteredOAuthProvider`** (`reboot.aio.auth.oauth_providers`)
for an authorization-code IdP with a pre-registered `client_id` /
`client_secret`; it already handles credentials, extra `scopes=`,
`store_tokens=`, and a fail-fast `validate()`. Subclass `OAuthProvider`
directly only for non-standard schemes (`Development` and `Anonymous` are
the in-tree examples).

**Start from the closest shipped provider** — read its source in the
installed `reboot` package and change only the endpoint URLs,
`_REQUIRED_SCOPE`, constructor extras (a base URL, realm, tenant), and
`token_service_id`:

- **`Auth0`** — the model for any OIDC IdP (Keycloak, Okta): code
  exchange, user id from the ID token's `sub`, a constructor extra
  (`domain=`) with its `validate()` check, full `store_tokens=True`
  support including `offline_access`.
- **`GitHub`** — the model for plain OAuth (no ID token): resolves the
  user id by calling the IdP's user-info API with the new access token.
- **`Google`** — a provider-specific refresh-token knob in
  `authorization_url` (`access_type=offline`).

You implement two methods; Reboot's OAuth server does the rest (its
`/__/oauth/...` endpoints, minting and verifying `state`, minting the
app's own access tokens, populating `context.auth.user_id`):

- **`authorization_url(state, redirect_uri) -> str`** — the IdP's
  authorize URL with your `client_id`, the scopes, `response_type=code`,
  and **`state` and `redirect_uri` passed through verbatim**: `state` is
  a JWT the server verifies on callback (CSRF), `redirect_uri` is the
  server's own `/__/oauth/callback`.
- **`exchange_code(code, redirect_uri) -> ExchangeResult`** — POST the
  code to the token endpoint (plain `aiohttp` / `httpx`) and resolve the
  user id: the OIDC `id_token`'s `sub`, or the IdP's user-info API.
  Raising here is safe — the server logs it and redirects with
  `access_denied`.

**Identity claims** (optional): declare the claims the IdP can deliver,
and the scope each needs, in the class-level `_AVAILABLE_CLAIMS`; accept
`claims=` and pass it to `super().__init__` (which rejects unavailable
claims and derives the scopes); pass the decoded ID token or userinfo
response through `self._presented_claims(...)` into
`ExchangeResult.claims`. That keeps only the requested claims, under
their presented names, so protocol claims (`exp`, `nonce`, …) and
IdP-specific names never leak; with no claims requested it returns
`None` and nothing is delivered. Claims go to the `User` type's
`set_claims` on every sign-in.

Optional hooks:

- **`validate()`** — raise `InputError` on missing/invalid config.
  Called once, when the provider is selected for the current
  environment, so a misconfigured `prod=` arm fails at startup. Call
  `super().validate()` first (see `Auth0.validate`).
- **`mount_routes(http)`** — provider-specific HTTP routes, rarely
  needed (`Development`'s login page; `Ory`'s settings-flow webhook). A
  route delivering identity changes between sign-ins may call
  `self._set_claims_if_exists(...)` (wired in by the OAuth server via
  `use_set_claims_if_exists` before `mount_routes` runs). See
  `Ory._webhook`.

Wire it like a shipped provider, then **tell the user** to register the
client in the IdP's console, obtain `client_id` / `client_secret`, and
add `<base-url>/__/oauth/callback` to its redirect-URI allowlist — only
they can, and the provider won't work until they do:

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

1. Override **`token_service_id`** with the state ID naming the service
   (e.g. `"sso.example.com"`); apps read tokens with
   `OAuthTokenManager.ref(<that id>).fetch(...)`.
2. When `self._store_tokens` is set, return `ExchangeResult.tokens` as
   an `OAuthTokens` (`rbt.std.oauth.v1.oauth_rbt`) with `access_token`,
   `refresh_token`, `expires_at`, `scopes`; otherwise `tokens=None`.
3. Add any refresh-token knob (`access_type=offline`, `offline_access`)
   in `authorization_url` only when `self._store_tokens` is set.

The server then stores the tokens encrypted and carries a prior
`refresh_token` forward when a sign-in omits one, as for shipped
providers (`auth-store-tokens.md`).

## Never

- Return an unstable user id from `exchange_code` — it becomes
  `context.auth.user_id` and the key of all user-keyed state. Use an
  OIDC `sub` or numeric account id, never an email that can change or
  anything session-scoped. It also fixes the user-ID namespace, so the
  provider-permanence rule of `auth-oauth-providers.md` applies.
- Rewrite or re-mint `state` / `redirect_uri` in `authorization_url` —
  the server verifies both on callback.
- Return tokens when `store_tokens` is off — apps that don't opt in
  must never carry these secrets.
- Put claims from an unverified source in `ExchangeResult.claims` —
  only an ID token straight from the token endpoint over TLS, or the
  userinfo endpoint over TLS.
- A claims-delivering route in `mount_routes` that doesn't authenticate
  its caller (a shared secret, a signature) — claims assert identity, so
  the route decides who can impersonate users.
- Write the provider from a blank page — adapt `Auth0` / `GitHub`.

## Limits

- `_set_claims_if_exists` delivers only to a `User` that already exists;
  it never creates one (webhooks fire instance-wide).
- Deliveries may repeat (`set_claims` is a full replace, idempotent by
  contract), and ordering is last-write-wins: a delayed retry can
  briefly overwrite a newer change until the next delivery or sign-in.
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
