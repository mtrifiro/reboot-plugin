---
name: web-app
description: Build complete Reboot Web Apps — a Reboot backend behind a standalone browser-facing React frontend, served at a normal URL (not embedded in an MCP host). Layers on top of the python skill for backend mechanics; covers what's specific to standalone Web Apps — no MCP front door, no UI() methods, normal React/Vite SPA scaffolding, and Reboot auth for browser users.
argument-hint: [<app-description>]
allowed-tools: Bash, Read, Write, Glob, Grep, Edit
---

# web-app — Build Reboot Web Apps

> **Version notices:** if `rbt` reports a version mismatch or a newer
> Reboot, follow the [upgrade skill](../upgrade/SKILL.md).

**Follow [`../build/SKILL.md`](../build/SKILL.md)** (design phase, state
model assessment, build steps, update flow). This skill holds the Web
App differences: a plain React SPA in a top-level `web/` Vite shell at a
normal URL, `VITE_REBOOT_URL`, `<RebootClientProvider>`, browser
sign-in, `allowed_origins`, and each step's reading list. A
dual-frontend app (browser SPA plus MCP front door, one backend) also
loads the [`mcp-ui` skill](../mcp-ui/SKILL.md) for `mcp=Tool()`, `UI()`
and MCPJam; see the [`app` skill](../app/SKILL.md) for what they share.

## When to Use

- Building or changing a Reboot Web App.
- Running an existing one (e.g. at session start): the
  [`run` skill](../run/SKILL.md).
- Production: the [`deploy` skill](../deploy/SKILL.md) — backend on
  Reboot Cloud, frontend on a static host under the user's own domain.

## How a Web App Differs From an MCP UI

The backend is identical; the deltas are on the frontend:

| Concern      | MCP UI (`mcp-ui`)                                        | Web App (this skill)                                                                      |
| ------------ | -------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| Front door   | MCP host (ChatGPT, Claude, …) creates a `User` per user. | Browser user signs in via `Application(oauth=...)`; same `User` per upstream identity.    |
| API exposure | `mcp=Tool()` on methods the AI calls.                    | `mcp=None` on every method (the keyword is required); calls go through the generated React client. |
| UI shape     | `UI()` methods → artifacts embedded in the MCP host.     | A normal SPA at `web/` opened at a URL.                                                   |
| Vite config  | Special — nested `dist/mcp/<ui-name>/index.html`.        | Stock single-page Vite output; no `viteSingleFile`, no nested-output override.            |
| Manual check | MCPJam inspector, from the setup wizard.                 | The browser; scenarios drive it through Playwright (`python/references/testing-web-app.md`). |
| `User` type  | Required — the MCP entry point.                          | Optional — only if your app needs per-user state.                                         |

## Auth in Web Apps

Identity, rules-before-tests, the production provider and
`allowed_origins` are build Step 4. Browser specifics:

- Reboot mounts its OAuth Authorization Server at `/__/oauth/*` and
  brokers sign-in against the upstream IdP. The session is an HttpOnly
  `rbt_session` cookie set by `/__/oauth/finish` and read as a bearer on
  every RPC, so servicers see only `context.auth.user_id` (as in MCP).
  `Development()` signs in at `/__/oauth/start`.
- **`allowed_origins`:** the SPA is always cross-origin from its backend
  (Vite's port in dev, its own host in production), so set
  `OAuth(..., allowed_origins=["https://app.example.com"])` with
  `oauth=`. `rbt dev run` auto-allows any `localhost` / `127.0.0.1`
  port, so a missing list is only a startup warning — until production
  refuses to start.
- **Safari and WKWebView can't sign in locally over plain http:** the
  sign-in cookies are `Secure` and WebKit doesn't exempt
  `http://localhost`, so the flow ends on
  `Missing pending-flow cookie. The sign-in flow may have expired`.
  Retrying doesn't help; sign in locally from another browser.

```python
from reboot.aio.applications import Application
from reboot.aio.auth.oauth import OAuth
from reboot.aio.auth.oauth_providers import (
    Development,
    Google,                       # or GitHub, Auth0, …
    OAuthProviderByEnvironment,
)
```

Providers (all arguments keyword-only):

| provider        | required arguments                        |
| --------------- | ----------------------------------------- |
| `Development()` | none — dev only, sign in as any of five identities |
| `Anonymous()`   | none — every visitor is a fresh identity  |
| `Google(...)`   | `client_id=`, `client_secret=`            |
| `GitHub(...)`   | `client_id=`, `client_secret=`            |
| `Auth0(...)`    | `domain=`, `client_id=`, `client_secret=` |
| `Ory(...)`      | `domain=`, `client_id=`, `client_secret=` |

- Every provider but `Anonymous` takes `claims=`, `Development()`
  included (`claims=["email", "name"]` fabricates them). The registered
  providers (all but `Development` and `Anonymous`) also take `scopes=`
  and `store_tokens=`.
- Register `/__/oauth/callback` as the redirect URI with the provider.
- Add `claims=[...]` to get the user's email or name: without it the app
  gets only an opaque user id and `set_claims` is never called. Never
  build a form asking a signed-in user to retype them
  (`python/references/auth-claims.md`).
- Read `mcp-ui/references/auth-oauth-providers.md` (frontend-neutral)
  only to write a custom provider or debug one provider's flow.

**Feeding identity into hooks.** With `oauth=`, call the `User` hook
with **no arguments** for the signed-in user's own state. An
explicit-id hook's id must be real on every render, never a placeholder
(`references/react-client.md`).

**Calling external APIs as the user** — tokens in an
`OAuthTokenManager`, call inside a `Workflow`
(`python/references/auth-external-api-calls.md`):

- Path A, the IdP you sign in with (`Google` / `GitHub` / `Auth0`): add
  `scopes=[...]` and `store_tokens=True`.
- Path B, any other service: run its OAuth flow with your own
  authorize/callback HTTP endpoints (callback registered
  `app_internal=True`) and call `OAuthTokenManager.store`.
- Path C, a pasted **API key**: `Ciphertext`.
- Never keep tokens in a plain `str` field or hand-roll `Ciphertext`
  (`python/references/stdlib-oauth-tokens.md`).

**Browser-side wiring** (provider and its `url`, generated hooks,
sign-in/sign-out, typed errors): read `references/react-client.md` at
the frontend step; don't reconstruct it from memory.

## Project Layout

```
<project-root>/
├── .python-version
├── .rbtrc                   # generate --react=web/src/api, --web=web/src/api
├── .mypy.ini                # Type-check config (python skill)
├── pytest.ini               # testpaths: tests; pythonpath: backend/src backend/api api
├── pyproject.toml
├── api/
│   └── <pkg>/v1/
│       └── <name>.py        # API definition (pydantic)
├── backend/
│   └── src/
│       ├── main.py          # Application entrypoint
│       └── servicers/
│           └── <name>.py    # Servicer implementation
├── tests/
│   ├── <capability>.feature  # One feature per capability
│   ├── <name>_test.py       # `application` fixture + `scenarios(...)`
│   └── web_test.py          # The scenarios that open the app
└── web/
    ├── .env.development     # VITE_REBOOT_URL=http://localhost:9991
    ├── package.json
    ├── tsconfig.json
    ├── tsconfig.app.json
    ├── tsconfig.node.json
    ├── vite.config.ts       # Stock Vite SPA config
    ├── index.html           # Single SPA entry, top of web/
    └── src/
        ├── main.tsx         # RebootClientProvider entry
        ├── App.tsx          # Routes + top-level component
        ├── pages/
        │   └── <page>.tsx
        └── api/             # Generated TypeScript client
                             # (output of `rbt generate --react=`)
```

Starting files: `../build/templates/web-app/`. `.rbtrc` points React
codegen at `web/src/api` (`generate --react=web/src/api` and
`generate --web=web/src/api`). Set `VITE_REBOOT_URL` in dev: the default
resolves to Vite's origin, not the backend (`references/react-client.md`).

## Which References to Read, and When

One group per step of [`../build/SKILL.md`](../build/SKILL.md). Read
each at its step, once, one per tool call; each appears in exactly one
group. Pattern references (`patterns-*.md`) are off the build path; read
one when its situation comes up (catalog in the `python` skill).

<!-- The lists below are generated from each reference's frontmatter
by tools/gen-index.py. Edit the frontmatter, not the lists. -->

> **Never read `mcp-ui/references/*` for a web app.** They cover the MCP
> frontend (`UI()` artifacts, MCPJam, nested `frontend/mcp/<name>/`
> Vite output, `mcp=Tool()` markers, popping a widget out into a web
> app) and produce MCP-UI-shaped code. Use
> [`references/react-client.md`](references/react-client.md) and the
> `python` references below. Sole exception:
> [mcp-ui/references/auth-oauth-providers.md](../mcp-ui/references/auth-oauth-providers.md)
> is frontend-neutral; read it when you pick a real provider.

**Before the API definition:**

<!-- generated:start reading-list front-door=web-app step=api -->
- `python/references/api-methods.md` — Which factory (`Reader`, `Writer`, `Transaction`, `Workflow`) and the servicer signature and context type each obliges; `factory=True` marks creation; `errors=`, `description=` and the required `mcp=`.
- `python/references/api-pydantic.md` — Every `Field` needs a tag and a zero-value default (non-zero is rejected at import time); wire declarations through `API(...)`; generated Request/Response names come from the method name, not the class.
- `python/references/state-actor-decomposition.md` — Split a Type whose fields cluster by unrelated concern (auth, persona, background engine, cache) into separate Types, or its writers serialize and `User` becomes a God actor.
- `python/references/state-collections.md` — Decide whether each "list of X" item is its own state Type (usually yes), then pick `list[Sub]`, `list[str]` of IDs, or an `OrderedMap`; never `list[Entity]` on a parent.
- `python/references/state-nested-models.md` — Group related fields into nested non-state `Model`s instead of parallel flat names, and mutate them in place; never put a state `Model` inside another state `Model`.
- `python/references/api-schema-evolution.md` — only when changing an API that is deployed or has persisted state.
- `python/references/api-errors.md` — only when the API declares typed errors.
- `python/references/state-scalar-fields.md` — only when a field holds a secret, token or PII, or you want a non-zero default.
<!-- generated:end -->

**Before the project shell** (`.rbtrc`, `pyproject.toml`,
`.mypy.ini`, `main.py`):

<!-- generated:start reading-list front-door=web-app step=shell -->
- `python/references/lifecycle-application-entry.md` — An `async def main()` that awaits `Application(servicers=[...], initialize=...).run()`; pass servicer classes, not instances; register stdlib libraries alongside your servicers.
- `python/references/lifecycle-project-setup.md` — Copy `build/templates/<front-door>/`: layout, `pyproject.toml`, `.gitignore`, `.mypy.ini`. No `__init__.py`; never edit `*_rbt.py`; mypy sees `self.state` as `Any` — use typed locals.
- `python/references/lifecycle-rbtrc.md` — `.rbtrc` is line-based `<subcommand> <flag>`, not YAML; `--application-name` (not `--name`) persists state; `--env-file` for secrets; `serve run` lines for production; named configs.
- `python/references/lifecycle-secrets.md` — only when the app needs secrets (API keys, OAuth client secrets).
<!-- generated:end -->

**Before the servicer:**

<!-- generated:start reading-list front-door=web-app step=servicer -->
- `python/references/lifecycle-initialize-hook.md` — Each `initialize` call runs once in the app's lifetime, not per boot, so a migration needs a new alias; create singletons here, not in `__init__`; failures retry forever.
- `python/references/rpc-calls.md` — Pass kwargs: `await ref.deposit(context, amount=10)`; writers and transactions can't be called from a WriterContext, even your own; caller identity does not travel; writer cycles deadlock.
- `python/references/servicer-constructor.md` — Set initial state in the `factory=True` method, never in `__init__`; a constructor runs once per actor (a second call aborts `StateAlreadyConstructed`); declare `Transaction(factory=True)` if it may construct others.
- `python/references/servicer-reader.md` — The reader signature must match the API file; mutating `self.state` is silently discarded; readers may call other readers, and a subscribed reader re-runs when any actor it read changes.
- `python/references/servicer-writer.md` — A writer mutates `self.state` on one actor only: no writes to other actors, no external calls, schedule only on itself; errors roll back the mutation; writers may return no response.
- `python/references/rpc-constructor-calls.md` — Call constructors as `<X>.<ctor>(context, id, ...)`, never through `.ref(id)`; `create` exists only if a factory is named that; outside a replayed key a second call aborts.
- `python/references/rpc-refs.md` — `self.ref().state_id`, never `self.state_id`; IDs are caller-supplied strings; checking whether an actor exists without hitting `StateNotConstructed`; `self.ref().schedule(...)`; reserved method names.
- `python/references/servicer-workflow.md` — only when you declared a `Workflow`.
- `python/references/agent-pydantic-ai.md` — only when the backend calls an LLM.
- `python/references/agent-tools.md` — only when an LLM agent needs tools that read or change Reboot state.
- `python/references/crypto-root-keys.md` — only when building your own key-derivation feature.
- `python/references/lifecycle-seeding.md` — only when the app seeds data in `initialize` or a script.
- `python/references/scheduling-basic.md` — only when deferring work with `schedule()` or `spawn(when=…)`.
- `python/references/servicer-transaction.md` — only when you declared a `Transaction`.
- `python/references/stdlib-ciphertext.md` — only when storing secrets or PII encrypted at rest.
- `python/references/stdlib-ordered-map.md` — only when the design uses an `OrderedMap`.
- `python/references/stdlib-queue.md` — only when the design uses a work `Queue`.
- `python/references/rpc-forall.md` — only when fanning one call out to many actors.
- `python/references/scheduling-recurring.md` — only when the app needs a recurring or cron job.
- `python/references/stdlib-presence.md` — only when tracking who is connected (presence).
- `python/references/stdlib-pubsub.md` — only when publishing to topics (pub/sub).
- `python/references/stdlib-item.md` — only when using the stdlib `Item` value envelope.
<!-- generated:end -->

**Before the authorizers** (build Step 4 — real rules on every
servicer before the first test; browser specifics in "Auth in Web
Apps" above):

<!-- generated:start reading-list front-door=web-app step=auth -->
- `python/references/auth-allow-deny.md` — `allow()` only for genuinely public endpoints, never to silence dev warnings, pass tests, or mark "internal-only" methods; `deny()` locks a method out; return an instance.
- `python/references/auth-allow-if.md` — `allow_if(all=[...])` or `allow_if(any=[...])`, never both, never nested; `all` short-circuits in order; `is_app_internal` in `any` turns anonymous callers' `Unauthenticated` into `PermissionDenied`.
- `python/references/auth-built-in-predicates.md` — `has_verified_token`, `is_app_internal` and `state_id_is_user_id` and their common compositions; a self-scheduled workflow needs `is_app_internal`; predicates always take `**kwargs`.
- `python/references/servicer-authorizer.md` — Write real rules on every servicer before the first test; list the tokenless call paths first; identity does not cross servicer calls; `oauth=` vs. the `token_verifier=` escape hatch.
- `python/references/auth-custom-predicates.md` — Per-method rules via `<Type>.Authorizer(method=rule, _default=rule)`; keyword-only predicates ending in `**kwargs`, annotated or `mypy` fails; check `context.app_internal` first; `PermissionDenied` vs. `Unauthenticated`.
- `python/references/auth-external-api-calls.md` — only when calling an external service's API as the user.
- `mcp-ui/references/auth-oauth-providers.md` — only when you pick a real (production) provider.
- `python/references/stdlib-oauth-tokens.md` — only when storing a user's OAuth tokens for an external service.
- `python/references/auth-claims.md` — only when you use claims or `set_claims`.
<!-- generated:end -->

**Before the frontend:**

<!-- generated:start reading-list front-door=web-app step=frontend -->
- `references/react-client.md` — Copy `build/templates/web-app/web/`; set `VITE_REBOOT_URL` in dev (the default resolves to Vite's origin); `server.host`, own port, `strictPort`; sign-in/out, accessible markup, typed errors.
- `python/references/react-generated-client.md` — What `rbt generate --react=` emits: `use<Type>()` overloads, three-field reader returns, mutations resolving to `{ response, aborted }` instead of throwing, typed errors, snake-to-camel naming.
<!-- generated:end -->

**Before the tests:**

<!-- generated:start reading-list front-door=web-app step=tests -->
- `python/references/patterns-idempotency.md` — What `IdempotencyUncertainError` means and when a retry needs an idempotency key; replayed calls return the first run's response; idempotent `create` / `initialize`; UUIDv7 for insertable records.
- `python/references/testing-features.md` — The built-in steps' exact spelling (who calls, `creates` / `does`, saved values, `eventually`, aborts, tasks), `@wip` / `@blocked`, feature / rule / scenario shape, custom steps, mocks.
- `python/references/testing-project-setup.md` — `tests/` layout; the template's `pytest.ini` (three paths, or generated `_rbt` imports fail) and fixture (`allowed_origins=[]`); `reboot[dev]`, no `pytest-asyncio`; never construct servicers directly.
- `python/references/testing-web-app.md` — The `frontend` fixture and web app steps, sign-in clicked through then bound, recordings, and the accessible markup (paired labels, named buttons, captioned tables) a page needs to be driven.
- `python/references/testing-external-context.md` — only when writing custom steps or harness tests.
- `python/references/testing-failure-recovery.md` — only when the app has a spawned task, a `Workflow`, or scheduled work.
- `python/references/testing-harness.md` — only when writing custom steps.
<!-- generated:end -->

Order of work around feature files (agree in English, tag `@wip`,
iterate on scenarios): the [`feature` skill](../feature/SKILL.md).

**Before running the app:** the [`run` skill](../run/SKILL.md).

Grepping installed framework source or a generated file? Stop: see
build's "Never Read Generated or Installed Source in the Main Thread".
