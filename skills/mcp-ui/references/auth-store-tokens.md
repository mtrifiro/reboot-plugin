---
title: Capturing the Identity Provider's Tokens with `store_tokens=True`
impact: HIGH
impactDescription: The `store_tokens=True` capture path is opt-in and easy to get subtly wrong — the wrong scope, a missing library, or the real provider absent in `dev=` all fail at runtime, not startup.
tags: auth, oauth, scopes, tokens, store_tokens, ciphertext, google, github, auth0, workflow, api, external
summary: "Extra `scopes=[...]` + `store_tokens=True` captures only the provider's own tokens (Auth0 yields an Auth0 token, not Google's); needs three libraries and crypto root keys; `Development()` issues none."
step: auth
applies: [mcp-ui]
always: false
when: "the app acts as the user at its own identity provider's API"
verified: 1.6.0
docs: ""
---

# Capturing the Identity Provider's Tokens with `store_tokens=True`

## When you are here

The app must call the API of the provider users sign in with
(`Application(oauth=...)`: `Google` / `GitHub` / `Auth0`) **as the
user**. This file is only the capture shortcut. Everything else — your
own OAuth endpoints for any other service, the read-back, the
in-`Workflow` call, refresh, erasure — is
[`python/references/auth-external-api-calls.md`](../../python/references/auth-external-api-calls.md).

## Do this

`scopes=` lists the **extra** OAuth scopes on top of the base identity
scope the provider always requests — only what your API calls need.
`store_tokens=True` makes the OAuth server capture the access/refresh
tokens at the code exchange (`/__/oauth/callback`) and store them
encrypted in the provider's `OAuthTokenManager`. Web apps signing in
through `oauth=` get the same capture.

```python
import os
from reboot.aio.applications import Application
from reboot.aio.auth.oauth import OAuth
from reboot.aio.auth.oauth_providers import (
    Google,
    OAuthProviderByEnvironment,
)
from reboot.std.ciphertext.v1.ciphertext import ciphertext_library
from reboot.std.collections.ordered_map.v1.ordered_map import (
    ordered_map_library,
)
from reboot.std.oauth.v1.oauth import oauth_library
from servicers.calendar import UserServicer

# Calendar *events* only — narrower than the full `calendar` scope.
_CALENDAR_SCOPE = "https://www.googleapis.com/auth/calendar.events"


def _google() -> Google:
    return Google(
        client_id=os.environ.get("GOOGLE_OAUTH_CLIENT_ID"),
        client_secret=os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET"),
        scopes=[_CALENDAR_SCOPE],   # on top of the base `openid` scope
        store_tokens=True,
    )


async def main() -> None:
    application = Application(
        servicers=[UserServicer],
        # oauth -> ciphertext -> ordered_map; all three, or startup fails.
        libraries=[oauth_library(), ciphertext_library(),
                   ordered_map_library()],
        oauth=OAuth(
            provider=OAuthProviderByEnvironment(
                # `Development()` issues no tokens, so the calendar
                # needs the real provider in dev too.
                dev=_google(),
                prod=_google(),
            ),
        ),
    )
    await application.run()
```

Read the tokens back with `OAuthTokenManager.ref(<service id>).fetch(...)`
inside a `Workflow` — `auth-external-api-calls.md`, "Use: inside a
`Workflow`".

## Never

- Expect a Google/GitHub token from `Auth0` — `store_tokens=True`
  captures the provider's **own** tokens. Through Auth0 (a broker) you
  store an **Auth0** token under the tenant-domain service ID; it
  authorizes Auth0's APIs, not Google Calendar. To reach the upstream
  API: retrieve the federated IdP token via Auth0's Management API
  (`GET /api/v2/users/{sub}`, needing a Management API token with
  `read:user_idp_tokens`; follow Auth0's "Call an Identity Provider API"
  docs), or run the upstream service's own flow (Path B of
  `auth-external-api-calls.md`), or sign in with `Google(...)` directly
  if its API is the point of the app.
- Use `store_tokens=True` for a service that isn't the sign-in provider
  (sign in with Google, call Slack) — there is no shortcut; use Path B.
- `dev=Development()` for a feature that needs provider tokens — it's a
  fake account picker and stores nothing, so `fetch` reports nothing.
  Put the real provider in `dev=` (with real credentials in dev).
- Request broad scopes "just in case" — request the least you need.

## Limits

- **At 1.6.0 the published wheel lacks `reboot.std.oauth`**, so
  `from reboot.std.oauth.v1.oauth import oauth_library` fails, and any
  provider with `store_tokens=True` fails at startup with
  `ModuleNotFoundError` (the library check imports that module).
  Observed on macOS / Python 3.12 (tool-checks-01, open).
- Startup requires the `oauth` + `ciphertext` libraries (and
  `ordered_map`, which `ciphertext` uses) when any provider stores
  tokens.
- `REBOOT_CRYPTO_ROOT_KEYS` backs the encryption; auto-provisioned under
  `rbt dev run`, part of your deploy in production
  (`python/references/stdlib-ciphertext.md`).
- Built-in service IDs: `Google` stores under `"google.com"`, `GitHub`
  under `"github.com"`, `Auth0` under its tenant domain.
- Refresh tokens: Google sends `access_type=offline` automatically;
  `Auth0` adds `offline_access`; a GitHub OAuth App never issues one
  (use a GitHub App with expiring user tokens). Reboot does not refresh
  access tokens.

## Scales as

- Not measured.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'reboot.std.oauth'` | The 1.6.0 wheel doesn't ship the `oauth` library | See Limits; no plugin-side fix at 1.6.0 |
| ``An OAuth provider with `store_tokens=True` needs the `oauth` and `ciphertext` libraries`` | Libraries not mounted (once the module ships) | Add all three to `libraries=` |

## See also

- [`auth-oauth-providers.md`](auth-oauth-providers.md) — choosing and configuring the provider
- [`python/references/auth-external-api-calls.md`](../../python/references/auth-external-api-calls.md) — Path B, the Workflow call
- [`python/references/stdlib-oauth-tokens.md`](../../python/references/stdlib-oauth-tokens.md) — `OAuthTokenManager` surface
