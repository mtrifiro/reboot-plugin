---
title: Capturing the Identity Provider's Tokens with `store_tokens=True`
impact: HIGH
impactDescription: The `store_tokens=True` capture path is opt-in and easy to get subtly wrong — the wrong scope, a missing library, or the real provider absent in `dev=` all fail at runtime, not startup.
tags: auth, oauth, scopes, tokens, store_tokens, ciphertext, google, github, auth0, workflow, api, external
summary: "`store_tokens=True` captures only the sign-in provider's tokens, none under `Development()`; extra `scopes=[...]`, three libraries, root keys."
step: auth
applies: [mcp-ui]
always: false
when: "the app acts as the user at its own identity provider's API"
verified: 1.6.0
docs: ""
---

# Capturing the Identity Provider's Tokens with `store_tokens=True`

## When you are here

The app calls the sign-in provider's API (`Application(oauth=...)`:
`Google` / `GitHub` / `Auth0`) **as the user**. This file is only the
capture shortcut; other services' OAuth endpoints, read-back, the
in-`Workflow` call, refresh and erasure are in
[`python/references/auth-external-api-calls.md`](../../python/references/auth-external-api-calls.md).

## Do this

`scopes=` lists only the **extra** scopes your API calls need, beyond the
base identity scope. `store_tokens=True` captures access/refresh tokens at
the code exchange (`/__/oauth/callback`) into the provider's
`OAuthTokenManager`, encrypted. Web apps signing in through `oauth=` get
the same capture.

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
                # `Development()` issues no tokens: real provider in dev.
                dev=_google(),
                prod=_google(),
            ),
        ),
    )
    await application.run()
```

Read back with `OAuthTokenManager.ref(<service id>).fetch(...)` inside a
`Workflow` (`auth-external-api-calls.md`, "Use: inside a `Workflow`").

## Never

- Expect a Google/GitHub token from `Auth0` — `store_tokens=True`
  captures the provider's **own** tokens: an **Auth0** token under the
  tenant-domain service ID, good for Auth0's APIs, not Google Calendar.
  For the upstream API: the federated IdP token via Auth0's Management API
  (`GET /api/v2/users/{sub}`, Management API token with
  `read:user_idp_tokens`; Auth0's "Call an Identity Provider API" docs),
  the upstream service's own flow (Path B, `auth-external-api-calls.md`),
  or `Google(...)` sign-in directly if its API is the point.
- Use `store_tokens=True` for a service that isn't the sign-in provider
  (sign in with Google, call Slack) — no shortcut; Path B.
- `dev=Development()` for a feature that needs provider tokens — the fake
  picker stores nothing. Real provider (and credentials) in `dev=`.
- Request broad scopes "just in case" — least you need.

## Limits

- **At 1.6.0 the published wheel lacks `reboot.std.oauth`**, so any
  provider with `store_tokens=True` fails at startup with
  `ModuleNotFoundError` until you install the plugin's vendored
  `reboot-std-oauth` package (`python/references/stdlib-oauth-tokens.md`,
  Do this; tool-checks-01, open upstream).
- Any provider storing tokens requires the `oauth` + `ciphertext` (+
  `ordered_map`) libraries at startup.
- `REBOOT_CRYPTO_ROOT_KEYS` backs the encryption; auto-provisioned under
  `rbt dev run`, part of your deploy in production
  (`python/references/stdlib-ciphertext.md`).
- Built-in service IDs: `Google` stores under `"google.com"`, `GitHub`
  under `"github.com"`, `Auth0` under its tenant domain.
- Refresh tokens: `Google` sends `access_type=offline`; `Auth0` adds
  `offline_access`; a GitHub OAuth App never issues one (use a GitHub App
  with expiring user tokens). Reboot does not refresh access tokens.

## Scales as

- Not measured.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| ``An OAuth provider with `store_tokens=True` needs the `oauth` and `ciphertext` libraries`` | Libraries not mounted | Add all three to `libraries=` |

## See also

- [`auth-oauth-providers.md`](auth-oauth-providers.md) — choosing and configuring the provider
- [`python/references/auth-external-api-calls.md`](../../python/references/auth-external-api-calls.md) — Path B, the Workflow call
- [`python/references/stdlib-oauth-tokens.md`](../../python/references/stdlib-oauth-tokens.md) — `OAuthTokenManager` surface
