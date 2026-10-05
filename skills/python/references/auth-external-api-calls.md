---
title: Calling External-Service APIs on the User's Behalf
impact: HIGH
impactDescription: Token capture is opt-in and easy to get subtly wrong — the wrong scope, a missing library, storing from a non-app-internal context, or an external call outside a Workflow all fail at runtime, not at startup. This is the host-agnostic recipe shared by MCP UIs and web apps.
tags: auth, oauth, tokens, store_tokens, oauth-token-manager, ciphertext, workflow, external, api, api-key, custom-endpoint, on-behalf, refresh-token, crypto-shred
summary: "Call external APIs as the user only inside a `Workflow`: capture OAuth tokens (`store_tokens=True` or your own flow) into `OAuthTokenManager`, or a user API key as `Ciphertext`; refresh and erase."
step: auth
applies: [mcp-ui, web-app, backend-only]
always: false
when: "calling an external service's API as the user"
verified: 1.6.0
docs: ""
---

# Calling External-Service APIs on the User's Behalf

## When you are here

The app acts **as the user** at an external service (their Google
Calendar, GitHub issues, Slack), possibly from background work later. Same
for MCP UIs and web apps: **capture** the credential once, encrypted;
**use** it inside a `Workflow`. `OAuthTokenManager` surface:
`stdlib-oauth-tokens.md`; `store_tokens=True` provider config: the `mcp-ui`
skill's `auth-store-tokens.md`. An app-wide key **you** hold (Stripe,
OpenAI) is an application secret (`lifecycle-secrets.md`).

## Do this

### Capture: pick the path

| The credential is… | Path | Libraries |
| --- | --- | --- |
| The `oauth=` sign-in provider's own token (`Google` / `GitHub` / `Auth0`) | **A**: `scopes=[...]` + `store_tokens=True` on the provider; no endpoints | `oauth_library()`, `ciphertext_library()`, `ordered_map_library()` |
| Any other service's OAuth token (sign in with Google, call Slack) | **B**: your own authorize + callback routes, then `OAuthTokenManager.store` | same three |
| An API key / personal access token the user pastes | **C**: `Ciphertext.encrypt`, keep the returned `state_id` | `ciphertext_library()`, `ordered_map_library()` |

**Path A** works on every frontend signing in through `oauth=`, but
captures only the provider's **own** tokens: `Auth0` yields an Auth0
token, not the upstream Google/GitHub one (ask Auth0 for the federated
token, or use Path B).

**Path B.** Register both routes on the `Application` (`.http`); the callback is
app-internal because `OAuthTokenManager` is app-internal only:

```python
application.http.get("/__/oauth/slack/authorize")(slack_authorize)
application.http.get("/__/oauth/slack/callback", app_internal=True)(
    slack_callback
)
```

**Authorize** redirects to the service's `/authorize` with your
`client_id`, scopes, the callback as `redirect_uri`, and an **HMAC-signed
`state`** carrying the signed-in `user_id`. **Callback** verifies `state`,
exchanges `code` at the token endpoint (plain `httpx` / `aiohttp`), stores:

```python
from reboot.aio.http import external_context
from rbt.std.oauth.v1.oauth_rbt import OAuthTokenManager, OAuthTokens
from starlette.responses import RedirectResponse

SLACK = "slack.com"  # any string naming the service.


async def slack_callback(request):
    # ... verify signed `state` -> `user_id`; exchange
    # `request.query_params["code"]` for the fields below ...
    tokens = OAuthTokens(
        access_token=access_token,
        refresh_token=refresh_token,  # omit if the service issues none.
        expires_at=expires_at,        # epoch seconds, if reported.
        scopes=granted_scopes,
    )
    # App-internal *because* the route registered `app_internal=True`.
    context = external_context(request)
    await OAuthTokenManager.ref(SLACK).store(
        context, user_id=user_id, tokens=tokens,
    )
    return RedirectResponse("/")
```

**Path C** — a `Transaction` the UI calls with the raw key; state keeps
only the reference:

```python
from rbt.std.ciphertext.v1.ciphertext_rbt import Ciphertext
from reboot.std.ciphertext.v1.ciphertext import (
    APP_SHARED_KEY_MANAGER_ID, make_associated_data,
)


class UserServicer(User.Servicer):

    async def connect_acme(
        self,
        context: TransactionContext,
        request: User.ConnectAcmeRequest,
    ) -> User.ConnectAcmeResponse:
        user_id = self.ref().state_id
        ciphertext, _ = await Ciphertext.encrypt(
            context,
            plaintext=request.api_key.encode(),
            associated_data=make_associated_data(
                user_id=user_id, purpose="acme-api-key",
            ),
            scope=f"user:{user_id}",  # crypto-shred unit (erasure).
            key_manager_id=APP_SHARED_KEY_MANAGER_ID,
        )
        self.state.acme_api_key_id = ciphertext.state_id
        return User.ConnectAcmeResponse()
```

Decrypt with the **same** `associated_data`; empty `acme_api_key_id` =
"not connected"; erase with
`KeyManager.ref(APP_SHARED_KEY_MANAGER_ID).shred(context, scope=...)`
(`stdlib-ciphertext.md`).

### Use: inside a `Workflow`

Read the credential and call out in one `Workflow` (`WorkflowContext` is
app-internal, as the token store requires), wrapped in `at_least_once` —
`at_most_once` when a duplicate is itself the failure
(`servicer-workflow-external.md`). `context.state_id` is the `user_id` on
a `User`-type servicer keyed by user ID.

```python
from rbt.std.oauth.v1.oauth_rbt import OAuthTokenManager
from reboot.std.oauth.v1.oauth import GOOGLE


class UserServicer(User.Servicer):

    @classmethod
    async def create_event(
        cls,
        context: WorkflowContext,
        request: User.CreateEventRequest,
    ) -> User.CreateEventResponse:
        try:
            stored = await OAuthTokenManager.ref(GOOGLE).fetch(
                context, user_id=context.state_id
            )
        except OAuthTokenManager.FetchAborted:
            # Nobody has connected this service yet.
            return User.CreateEventResponse(ok=False, message=_CONNECT)
        if not stored.found:
            return User.CreateEventResponse(ok=False, message=_CONNECT)
        tokens = stored.tokens

        async def do_create():
            # Plain httpx/aiohttp in a helper module.
            return await calendar_api.create_event(
                access_token=tokens.access_token, summary=request.summary,
            )

        result = await at_least_once("create:post", context, do_create)
        return User.CreateEventResponse(ok=True, event=...)
```

UI shape: the `Workflow` writes a **snapshot** to state, a `Reader`
exposes it, and a UI-invoked `Writer` `schedule()`s the workflow (a
`Writer` can't await one).

**Erase** a user's tokens by shredding their scope in the service's key
manager; `fetch` then reports `found=False`:

```python
from rbt.std.ciphertext.v1.ciphertext_rbt import KeyManager
from reboot.std.oauth.v1.oauth import GOOGLE, _key_manager_id

await KeyManager.ref(_key_manager_id(GOOGLE)).shred(context, scope=user_id)
```

## Never

- The outbound HTTP call in a `Reader` / `Writer` / `Transaction` —
  retries and effect validation re-issue it. Only in a `Workflow`, in a
  durability primitive.
- `context.auth.user_id` in that `Workflow` — scheduled / app-internal
  calls don't reliably populate `context.auth`. Use `context.state_id`.
- Tokens or API keys in a `str` field, or OAuth tokens in hand-rolled
  `Ciphertext` — use `OAuthTokenManager` (A, B) or `Ciphertext` (C).
- A user API key in `OAuthTokenManager` — it is for OAuth tokens.
- `app_internal=True` on a route that acts on unvalidated input — it
  bypasses authorizers for **any** caller. Only on a callback that
  verifies the `state` you issued.
- `app_internal=True` on a templated path (`/x/{id}`) — the app-internal
  context is given only when the request path equals the declared string,
  so a path parameter silently yields an external context and
  app-internal-only calls are refused. Literal path; variables in the
  query string (1.6.0 `reboot/aio/http.py`).
- Crashing on "not connected" — handle `found=False` and `FetchAborted`
  with a connect / re-authenticate path.

## Limits

- **At 1.6.0, Paths A and B cannot run from the published wheel**: it
  lacks `reboot.std.oauth` (`oauth_library`, `GOOGLE`, `_key_manager_id`,
  the `OAuthTokenManager` servicer), observed on macOS / Python 3.12.
  `store_tokens=True` fails at startup with `ModuleNotFoundError`
  (tool-checks-01, open; `stdlib-oauth-tokens.md` § Limits). Path C
  needs only `ciphertext` and works.
- Reboot stores what the token endpoint returns, carrying a prior
  `refresh_token` forward when a capture omits it. It does **not** refresh
  expired access tokens: check `expires_at`, call the token endpoint yourself.
- Refresh tokens: **Google** only on first consent (Reboot sends
  `access_type=offline`); **Auth0** only with `offline_access` (added when
  `store_tokens=True`); **GitHub** OAuth Apps never (token doesn't expire),
  a GitHub App with "Expire user authorization tokens" issues both.
- `store` replaces the user's tokens wholesale; no read and write of the
  same manager in one transaction.
- `REBOOT_CRYPTO_ROOT_KEYS` is auto-provisioned under `rbt dev run` and
  on Reboot Cloud.

## Scales as

- Not measured.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'reboot.std.oauth'` | The 1.6.0 wheel lacks the `oauth` library (Paths A/B) | See Limits; Path C still works |
| `FetchAborted` | Nothing ever stored for this service | "Connect" path |

## See also

- [`stdlib-oauth-tokens.md`](stdlib-oauth-tokens.md) — `OAuthTokenManager` surface
- [`servicer-workflow-external.md`](servicer-workflow-external.md) — durability primitive decision table
- [`stdlib-ciphertext.md`](stdlib-ciphertext.md) — API keys, shred scopes
