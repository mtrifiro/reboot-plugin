---
title: Store Provider OAuth Tokens in `OAuthTokenManager`, Not Hand-Rolled `Ciphertext`
impact: HIGH
impactDescription: OAuth access/refresh tokens are secrets at rest; the stdlib manager encrypts, indexes, and crypto-shreds them per user for you — a plain `str` field leaks them, and hand-rolling `Ciphertext` re-implements what already exists.
tags: stdlib, oauth, tokens, access-token, refresh-token, store-tokens, ciphertext, encryption, crypto-shred, google, github, secret
summary: "Store provider access/refresh tokens in `OAuthTokenManager`, never a `str` field or hand-rolled `Ciphertext`; three libraries required (the `oauth` one is missing from the 1.6.0 wheel); app-internal only."
step: auth
applies: [mcp-ui, web-app, backend-only]
always: false
when: "storing a user's OAuth tokens for an external service"
verified: 1.6.0
docs: ""
---

# Store Provider OAuth Tokens in `OAuthTokenManager`

## When you are here

Storing or reading a user's OAuth access/refresh tokens for an external
service (Google, GitHub, Slack, …). This is the `OAuthTokenManager`
surface; the end-to-end flow (`store_tokens=True`, your own
authorize/callback, the in-`Workflow` call, refresh, erasure) is
`auth-external-api-calls.md`. Non-OAuth secrets (pasted API key, PII):
`Ciphertext` (`stdlib-ciphertext.md`).

## Do this

One `OAuthTokenManager` per external service, keyed by `user_id`; its state
ID names the service (`GOOGLE` / `GITHUB` constants, or any string, e.g.
`"slack.com"`). Each manager encrypts under its own `KeyManager`, each
user's tokens under a crypto-shred scope of their `user_id`, so one user
can be erased alone.

Mount all three libraries (manager → `Ciphertext` → `OrderedMap`) and
import the manager:

```python
from reboot.std.oauth.v1.oauth import oauth_library, GOOGLE, GITHUB
from reboot.std.ciphertext.v1.ciphertext import ciphertext_library
from reboot.std.collections.ordered_map.v1.ordered_map import (
    ordered_map_library,
)
from rbt.std.oauth.v1.oauth_rbt import OAuthTokenManager, OAuthTokens
# also: from reboot.aio.auth import OAuthTokenManager, OAuthTokens

Application(
    servicers=[...],
    libraries=[oauth_library(), ciphertext_library(), ordered_map_library()],
)
```

`OAuthTokens`:

| Field | Type | Notes |
| --- | --- | --- |
| `access_token` | `str` | Bearer token for the provider's API. |
| `refresh_token` | optional `str` | Unset (`HasField` false) if none was issued. |
| `expires_at` | optional `int64` | Absolute expiry, epoch seconds; unset if unknown. |
| `scopes` | repeated `str` | Scopes the provider actually granted. |

**Fetch** (reader):

```python
response = await OAuthTokenManager.ref(GOOGLE).fetch(
    context, user_id=user_id,
)
if response.found:
    access_token = response.tokens.access_token
```

**Store** (transaction) — only when you capture tokens yourself from a
service other than the `oauth=` sign-in provider (the only path in a web
app without `oauth=`):

```python
await OAuthTokenManager.ref("slack.com").store(
    context,                  # must be app-internal (e.g. from an
    user_id=user_id,          # `app_internal=True` callback route).
    tokens=OAuthTokens(
        access_token=access_token,
        refresh_token=refresh_token,  # omit if none.
        scopes=granted_scopes,
    ),
)
```

For the sign-in provider's **own** tokens under `Application(oauth=...)`,
don't `store`: `store_tokens=True` captures them at the code exchange; you
only `fetch` (`auth-external-api-calls.md`, Path A).

## Never

- Tokens in a `str` state field — plaintext at rest.
- Hand-rolled `Ciphertext` for provider OAuth tokens — the manager
  already encrypts, indexes by `user_id`, and shreds per user.
- A user-pasted API key in `OAuthTokenManager` — that is `Ciphertext`
  (`auth-external-api-calls.md`, Path C).
- Leaving out any of `oauth_library()`, `ciphertext_library()`,
  `ordered_map_library()`.
- Calling `store` / `fetch` from an untrusted, external context — they
  are app-internal only.

## Limits

- **The 1.6.0 wheel lacks `reboot.std.oauth`** (observed on macOS /
  Python 3.12; the `manylinux_2_34_x86_64` wheel's file list has no
  `reboot/std/oauth/` either). `oauth_library`, `GOOGLE`, `GITHUB` and
  `_key_manager_id` cannot be imported, and no `OAuthTokenManager`
  servicer implementation ships to mount — only the generated
  `rbt.std.oauth.v1.oauth_rbt` client (tool-checks-01, open). The
  built-in providers use the service IDs `"google.com"` (`Google`) and
  `"github.com"` (`GitHub`); `Auth0` uses its tenant domain.
- `store` replaces the user's tokens wholesale, but carries a prior
  `refresh_token` forward when the new `tokens` leaves it unset.
- No read and write of the same manager in one transaction; to merge,
  `fetch` in a separate call first.
- `fetch` returns `found=False` when nothing is stored for the user or
  their scope was shredded; before the first `store` (which constructs the
  manager) it aborts (`FetchAborted`, `StateNotConstructed`).
- Reboot does not refresh expired access tokens; check `expires_at`.
- `REBOOT_CRYPTO_ROOT_KEYS` backs the encryption; auto-provisioned under
  `rbt dev run` and on Reboot Cloud.

## Scales as

- Not measured.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'reboot.std.oauth'` | The 1.6.0 wheel does not ship the `oauth` library; also raised at startup by any provider with `store_tokens=True` (the library check imports it) | No fix in the plugin at 1.6.0; see Limits |
| `FetchAborted` | Nothing has ever been stored for this service | Treat as "not connected" |

## See also

- [`auth-external-api-calls.md`](auth-external-api-calls.md) — capture, use, refresh, erase
- [`stdlib-ciphertext.md`](stdlib-ciphertext.md) — non-OAuth secrets, shred scopes
- [`servicer-workflow-external.md`](servicer-workflow-external.md) — outbound calls in Workflows
