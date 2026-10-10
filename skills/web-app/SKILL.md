---
name: web-app
description: Build complete Reboot Web Apps — a Reboot backend behind a standalone browser-facing React frontend, served at a normal URL (not embedded in an MCP host). Use when the prompt names a URL, a page or a website, or names no front door (the default). Layers on the build skill's shared design-and-build flow; holds what is specific to Web Apps — the web/ Vite shell, VITE_REBOOT_URL, browser sign-in and allowed_origins — and each build step's reading list. The backend stays ready for an MCP UI.
argument-hint: [<app-description>]
allowed-tools: Bash, Read, Write, Glob, Grep, Edit
---

# web-app — Build Reboot Web Apps

> **Version notices:** if `rbt` reports a version mismatch or a newer
> Reboot, follow the [upgrade skill](../upgrade/SKILL.md).

A web app is one of a Reboot app's two **front doors** (the ways people
reach its backend; [`app` skill](../app/SKILL.md)): a website in a
browser.

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
| API exposure | `mcp=Tool()` on methods the AI calls.                    | `mcp=None` on every method until an MCP UI is added (the keyword is required); calls go through the generated React client. |
| UI shape     | `UI()` methods → artifacts embedded in the MCP host.     | A normal SPA at `web/` opened at a URL.                                                   |
| Vite config  | Special — nested `dist/mcp/<ui-name>/index.html`.        | Stock single-page Vite output; no `viteSingleFile`, no nested-output override.            |
| Manual check | MCPJam inspector, from the setup wizard.                 | The browser; scenarios drive it through Playwright (`python/references/testing-web-app.md`). |
| `User` type  | Required — the MCP entry point.                          | Required too — it owns per-user state and keeps the backend ready for an MCP UI.          |

## Auth in Web Apps

Identity, rules-before-tests, the production provider and
`allowed_origins` are build Step 4. Browser specifics:

- Reboot mounts its OAuth Authorization Server at `/__/oauth/*` and
  brokers sign-in against the upstream IdP. The session is an HttpOnly
  `rbt_session` cookie set by `/__/oauth/finish` and read as a bearer on
  every RPC, so servicers see only `context.auth.user_id` (as in MCP).
  `Development()` signs in at `/__/oauth/start`.
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
- With `claims=[...]`, never build a form asking a signed-in user to
  retype their email or name (`python/references/auth-claims.md`).
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

## Project Layout

The template's tree (`../build/templates/web-app/`, each file in its
README), plus pages under `web/src/pages/`, one
`tests/<capability>.feature` per capability, and `tests/web_test.py` for
the scenarios that open the app. `.rbtrc` points React codegen at
`web/src/api` (`generate --react=`, nothing else).

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

_Design_ — until the user accepts the domain model and feature files
(build skill, "Accept the Design"):

**Before the API definition:**

<!-- generated:start reading-list front-door=web-app step=api -->
- `python/references/api-methods.md` — The factory fixes the servicer's context type, and `mcp=` is required; `Reader`/`Writer`/`Transaction`/`Workflow`, `factory=True`, `errors=`, `description=`.
- `python/references/api-pydantic.md` — A non-zero `Field` default is rejected at import; tags, zero defaults, `API(...)` wiring, Request/Response naming.
- `python/references/state-actor-decomposition.md` — A Type with unrelated field clusters serializes writers and grows a God `User`; split it into separate Types.
- `python/references/state-collections.md` — Never `list[Entity]` on parents; decide if each item is its own Type, then `list[Sub]`, ID list or `OrderedMap`.
- `python/references/state-nested-models.md` — Never a state `Model` inside another; group related fields in nested non-state `Model`s, mutated in place.
- `python/references/api-schema-evolution.md` — only when changing an API that is deployed or has persisted state.
- `python/references/api-errors.md` — only when the API declares typed errors.
- `python/references/state-scalar-fields.md` — only when a field holds a secret, token or PII, or you want a non-zero default.
<!-- generated:end -->

_Prove_ — building to the accepted design:

**Before the project shell** (`.rbtrc`, `pyproject.toml`,
`.mypy.ini`, `main.py`):

<!-- generated:start reading-list front-door=web-app step=shell -->
- `python/references/lifecycle-application-entry.md` — Pass servicer classes, not instances, and register stdlib libraries; `async def main()` awaiting `Application(servicers=[...], initialize=...).run()`.
- `python/references/lifecycle-project-setup.md` — Never add `__init__.py` or edit `*_rbt.py`; copy `build/templates/<front-door>/`; mypy sees `self.state` as `Any`: typed locals.
- `python/references/lifecycle-rbtrc.md` — `.rbtrc` is line-based, not YAML; `--application-name` not `--name`; `--env-file` for secrets; `serve run` lines; named configs.
- `python/references/lifecycle-secrets.md` — only when the app needs secrets (API keys, OAuth client secrets).
<!-- generated:end -->

**Before the servicer:**

<!-- generated:start reading-list front-door=web-app step=servicer -->
- `python/references/lifecycle-initialize-hook.md` — Each `initialize` call runs once per app lifetime, not per boot; migrations need new aliases; failures retry forever.
- `python/references/lifecycle-seeding.md` — Concurrent or one-per-record seeding hangs or takes minutes; seed in sequential batched transactions with stable per-call aliases.
- `python/references/rpc-calls.md` — Writers can't call writers or transactions, even their own; caller identity doesn't travel; writer cycles deadlock; pass kwargs.
- `python/references/servicer-constructor.md` — Never set initial state in `__init__`; a second call aborts `StateAlreadyConstructed`; use `Transaction(factory=True)` if it constructs others.
- `python/references/servicer-reader.md` — Mutating `self.state` in a reader is silently discarded; signature must match the API; reader-to-reader calls; subscription re-runs.
- `python/references/servicer-writer.md` — Writers mutate one actor: no writes to others, no external calls, schedule only on self; errors roll back.
- `python/references/rpc-constructor-calls.md` — Constructors aren't on `.ref(id)` and a second call aborts; call `<X>.<ctor>(context, id, ...)`; get-or-create.
- `python/references/rpc-refs.md` — `self.state_id` raises, use `self.ref().state_id`; probing existence without `StateNotConstructed`; caller-supplied IDs; reserved method names.
- `python/references/servicer-workflow.md` — only when you declared a `Workflow`.
- `python/references/agent-pydantic-ai.md` — only when the backend calls an LLM.
- `python/references/agent-tools.md` — only when an LLM agent needs tools that read or change Reboot state.
- `python/references/crypto-root-keys.md` — only when building your own key-derivation feature.
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
- `python/references/auth-allow-deny.md` — `allow()` to silence warnings, pass tests or mark internal methods makes them public; `deny()` blocks everyone; `return allow()`.
- `python/references/auth-allow-if.md` — `is_app_internal` in `any` turns anonymous `Unauthenticated` into `PermissionDenied`; `allow_if(all=[...])` or `allow_if(any=[...])`, never both or nested; `all` short-circuits.
- `python/references/auth-built-in-predicates.md` — Token predicates alone deny servicer-to-servicer calls; `has_verified_token`, `is_app_internal`, `state_id_is_user_id` and compositions.
- `python/references/servicer-authorizer.md` — Without real rules every external call is denied; identity doesn't cross servicer calls; tokenless paths; `oauth=` vs `token_verifier=`.
- `python/references/auth-custom-predicates.md` — Predicates must be keyword-only with `**kwargs` and check `context.app_internal` first; per-method rules via `<Type>.Authorizer(method=rule, _default=rule)`.
- `python/references/auth-external-api-calls.md` — only when calling an external service's API as the user.
- `mcp-ui/references/auth-oauth-providers.md` — only when you pick a real (production) provider.
- `python/references/auth-roles.md` — only when staff sign in with roles (a manager, a host, a server; editors and readers).
- `python/references/stdlib-oauth-tokens.md` — only when storing a user's OAuth tokens for an external service.
- `python/references/auth-claims.md` — only when you use claims or `set_claims`.
<!-- generated:end -->

**Before the frontend:**

<!-- generated:start reading-list front-door=web-app step=frontend -->
- `references/react-client.md` — An unset `VITE_REBOOT_URL` points at Vite's origin; copy `build/templates/web-app/web/`; own port, `strictPort`, sign-in, typed errors.
- `python/references/react-generated-client.md` — Mutations resolve to `{ response, aborted }`, never throw; `rbt generate --react=` output: `use<Type>()` overloads, reader returns, naming.
- `references/ui-design.md` — Brief, Reboot's brand by default (a user's brand replaces it), primary view by task, page anatomy, labeled controls, light/dark toggle, restyle by token values, screenshot review.
<!-- generated:end -->

**Before the tests:**

<!-- generated:start reading-list front-door=web-app step=tests -->
- `python/references/testing-features.md` — Built-in steps match their exact spelling; who calls, `creates` / `does`, saved values, `eventually`, aborts, `@wip`, custom steps.
- `python/references/testing-project-setup.md` — Missing `pytest.ini` paths break `_rbt` imports; no `pytest-asyncio`; `tests/` layout, fixture with `allowed_origins=[]`, `reboot[dev]`.
- `python/references/testing-web-app.md` — Pages need accessible markup (labels, named buttons) to be driven; the `frontend` fixture, web steps, clicked-through sign-in, recordings.
- `python/references/testing-external-context.md` — only when writing custom steps or harness tests.
- `python/references/testing-failure-recovery.md` — only when the app has a spawned task, a `Workflow`, or scheduled work.
- `python/references/testing-harness.md` — only when writing custom steps.
<!-- generated:end -->

Order of work around feature files (agree in English, tag `@wip`,
iterate on scenarios): the [`feature` skill](../feature/SKILL.md).

**Before running the app:** the [`run` skill](../run/SKILL.md).

Grepping installed framework source or a generated file? Stop: see
build's "Never Read Generated or Installed Source in the Main Thread".
