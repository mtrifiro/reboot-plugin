---
name: web-app
description: Build complete Reboot Web Apps — a Reboot backend behind a standalone browser-facing React frontend, served at a normal URL (not embedded in an MCP host). Layers on top of the python skill for backend mechanics; covers what's specific to standalone Web Apps — no MCP front door, no UI() methods, normal React/Vite SPA scaffolding, and Reboot auth for browser users.
argument-hint: [<app-description>]
allowed-tools: Bash, Read, Write, Glob, Grep, Edit
---

# web-app — Build Reboot Web Apps

> **Version notices:** if `rbt` reports a version mismatch or that a
> newer Reboot is available, the [upgrade skill](../upgrade/SKILL.md)
> says how and when to react.

Build complete Reboot Web Apps from a user description: a Reboot
backend behind a standalone React frontend served at a normal URL.

> **Reads from `python`.** This skill is the standalone-web-frontend
> layer on top of the Reboot Python framework. Anything about
> Servicers, Reboot contexts, refs, scheduling primitives,
> backend LLM / agent calls, error types, the testing harness,
> the `.rbtrc` shape, or pydantic API defaults belongs in
> `python` — load those references for those concerns. This
> skill covers what's _specific_ to standalone Web
> Apps: a plain React SPA at `web/`, the generated TypeScript hooks
> from `rbt generate --react=...`, regular auth flows (login form /
> cookies / OAuth), and the cross-cutting rules unique to that
> layer.

> **Dual-frontend apps are supported.** A single app can serve both
> a standalone web SPA _and_ an MCP front door from the same
> backend — they share `oauth=...`, the same `User` actor per
> upstream identity, and the same servicer code. If your app needs
> both frontends, also load the
> [`mcp-ui` skill](../mcp-ui/SKILL.md) for the MCP-specific
> additions (`mcp=Tool()`, `UI()`, MCPJam).
> This skill alone covers the web side.

## When to Use

- Building a new Reboot Web App from a description.
- Adding features, state, or UI to an existing Reboot Web App.
- Modifying state model, methods, or React UI in a Reboot Web App.
- Running an existing Reboot Web App — e.g. at the start of a new
  session: load the [`run` skill](../run/SKILL.md), which detects
  the app type and starts the backend and frontend.
- Putting a finished Web App in production — load the
  [`deploy` skill](../deploy/SKILL.md): backend on Reboot Cloud,
  frontend on a static host under the user's own custom domain.

## How a Web App Differs From an MCP UI

The Reboot backend is identical. The deltas are all on the frontend:

| Concern      | MCP UI (`mcp-ui`)                                        | Web App (this skill)                                                                      |
| ------------ | -------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| Front door   | MCP host (ChatGPT, Claude, …) creates a `User` per user. | Browser user signs in via `Application(oauth=...)`; same `User` per upstream identity.    |
| API exposure | `mcp=Tool()` on writer/transaction methods.              | Methods exposed only through the generated React client.                                  |
| UI shape     | `UI()` methods → artifacts embedded in the MCP host.     | A normal SPA at `web/` opened at a URL.                                                   |
| Vite config  | Special — nested `dist/<ui-path>/index.html` for MCP.    | Stock single-page Vite output.                                                            |
| Test surface | MCPJam inspector.                                        | Scenarios that drive the app through Playwright (`python/references/testing-web-app.md`). |
| `User` type  | Required — the MCP entry point.                          | Optional — only if your app needs per-user state.                                         |

Backend mechanics (state, methods, Servicers, workflows, refs,
scheduling, stdlib actors, errors, auth predicates, testing) are
**unchanged** — load them from `python`.

## Auth in Web Apps

Web apps wire identity via
`Application(oauth=OAuth(provider=OAuthProviderByEnvironment(dev=Development(), prod=Google(...))))`
— the same parameter MCP UIs use. Reboot mounts its
built-in OAuth Authorization Server at `/__/oauth/*` and brokers
sign-in against the configured upstream IdP. Browser sessions
are carried in an HttpOnly `rbt_session` cookie set by
`/__/oauth/finish`; the framework reads it as a bearer on every
RPC, so user code only sees `context.auth.user_id` (same shape
as MCP).

> **`token_verifier=` is the escape hatch, not the default.** Use
> it only when you need to integrate with an IdP that the
> built-in `oauth=` providers don't cover (e.g. an enterprise
> SAML/OIDC broker you can't wrap as an `OAuthProvider`
> subclass), or when you need custom token semantics. For
> standard Google/GitHub/Auth0/anonymous sign-in, prefer
> `oauth=...`. The two compose: when both are set, Reboot's own
> verifier runs first and any token it has no opinion on
> (anything that is not a Reboot-minted access JWT) falls
> through to yours.

The imports, so you don't have to go looking for them:

```python
from reboot.aio.applications import Application
from reboot.aio.auth.oauth_providers import (
    Development,
    Google,                       # or GitHub, Auth0, …
    OAuthProviderByEnvironment,
)
```

Recommended sequence:

1. **Early development (no provider chosen yet):** configure
   `oauth=OAuth(provider=OAuthProviderByEnvironment(dev=Development(), prod=None))`.
   `Development()` is a built-in fake account picker that lets
   you sign in as any identity at `/__/oauth/start`; `prod=None`
   fails fast at startup if you accidentally `rbt serve` without
   choosing a real provider. **Write `authorizer()` rules before
   the tests:** `rbt dev` allows calls on a Servicer with no
   `authorizer()` (with a warning naming each method), but the
   test harness denies them, as production does. Do **not** paper
   this over with `allow()`;
   `allow()` means "public, unauthenticated internet endpoint"
   and survives into production.
2. **Before `rbt serve` / Reboot Cloud:** set `prod=Google(...)`
   (or `GitHub(...)`, `Auth0(...)`, your own `OAuthProvider`
   subclass), then add `allow_if(...)` rules to every Servicer
   that should be externally reachable. See
   `python/references/servicer-authorizer.md`,
   `python/references/auth-allow-if.md`, and
   `python/references/auth-built-in-predicates.md`. The
   The providers and what each needs:

   All arguments are keyword-only.

   | provider        | required arguments                        |
   | --------------- | ----------------------------------------- |
   | `Development()` | none — dev only, sign in as any identity  |
   | `Anonymous()`   | none — every visitor is a fresh identity  |
   | `Google(...)`   | `client_id=`, `client_secret=`            |
   | `GitHub(...)`   | `client_id=`, `client_secret=`            |
   | `Auth0(...)`    | `domain=`, `client_id=`, `client_secret=` |
   | `Ory(...)`      | `domain=`, `client_id=`, `client_secret=` |

   The registered providers (everything but `Development` and
   `Anonymous`) also take `scopes=`, `claims=`, and
   `store_tokens=`; `Development()` takes `claims=` too, so
   everything but `Anonymous` accepts it. Register `/__/oauth/callback` as the redirect
   URI with the provider.

   Add `claims=[...]` when you need identity fields such as the
   user's email, and `store_tokens=True` only when you will call
   that provider's own API as the user. **Choose deliberately
   before real users exist**: `context.auth.user_id` is namespaced
   per provider, so switching providers after launch strands every
   existing user's state. Only reach for
   [mcp-ui/references/auth-oauth-providers.md](../mcp-ui/references/auth-oauth-providers.md)
   if you need to write a custom provider or debug a specific
   provider's flow. In unit tests, keep
   `token_verifier=<your IdP verifier>` exactly as in production —
   the test harness's OAuth server verifies the impersonation token
   minted by `await rbt.create_external_context_as(name, user_id)`,
   and a custom bearer a test constructs by hand still hits your IdP
   verifier; the authorizer rules run for real either way.

3. **Public, unauthenticated endpoints** (health checks, public
   sign-up, public catalog reads): mark these explicitly with
   `allow()`. That's the one legitimate use.

### Feeding the user's identity into hooks

With `Application(oauth=...)` the signed-in user's own state needs
no id-threading: call the `User` hook with **no arguments**. For
explicit-id hooks the rule is that the id must be real on every
render — never a placeholder — which is covered with the rest of
the hook mechanics in
[`references/react-client.md`](references/react-client.md).

### Calling external APIs on the user's behalf

To act **as the user** at an external service (call their Slack,
Google, a partner API), store that service's OAuth tokens encrypted in
an `OAuthTokenManager` and make the call inside a `Workflow`. When the
API belongs to the identity provider you already sign in with via
`Application(oauth=...)` (`Google` / `GitHub` / `Auth0`), use the
`store_tokens=True` shortcut: add the extra `scopes=[...]` your calls
need and the OAuth server captures the provider's tokens at sign-in
(Path A in `python/references/auth-external-api-calls.md`). For any
other service, run that service's OAuth flow yourself with your own
authorize/callback HTTP endpoints (a callback registered
`app_internal=True`) and call `OAuthTokenManager.store`. The full
host-agnostic recipe — endpoints, storage, reading tokens back, the
in-`Workflow` call, refresh, and erasure — is
`python/references/auth-external-api-calls.md` (Path B). Never store
tokens in a plain `str` field or hand-roll `Ciphertext`
(`python/references/stdlib-oauth-tokens.md`). If the service doesn't do
OAuth at all and the user pastes an **API key** instead, that key goes
through `Ciphertext` (the ciphertext id kept in state) — Path C in the
same recipe.

### Browser-side wiring (React)

All of it — the provider (and the `url` it must be given), the
generated hook surface, sign-in/sign-out, reading typed errors, and
why a hook's `id` must be real on every render — is in
[`references/react-client.md`](references/react-client.md). Read it
at the frontend step; don't reconstruct it from memory here.

## Which References to Read, and When

Everything you read stays in the conversation and is re-sent on
every later turn, so **read each reference at the step that needs
it** — not all of them up front — and read each one **once**. The
groups below are in build order; each reference appears in exactly
one of them. A line ending *Only when …* is skipped unless that is
true of your app. Pattern references (`patterns-*.md`) are not on
the build path; read one when its situation comes up (catalog in
the `python` skill).

<!-- The lists below are generated from each reference's frontmatter
by tools/gen-index.py. Edit the frontmatter, not the lists. -->

> **Never read `mcp-ui/references/*` for a web app.** They cover
> the MCP frontend — `UI()` artifacts, the MCPJam inspector, the
> nested `frontend/mcp/<name>/` Vite output, `mcp=Tool()` markers,
> popping a widget out into a web app. Reaching into them costs
> context and produces MCP-UI-shaped code (`mcp=None` on every
> method of an app with no MCP frontend). The web equivalents are
> [`references/react-client.md`](references/react-client.md) and the
> `python` references named below. The single exception is
> [mcp-ui/references/auth-oauth-providers.md](../mcp-ui/references/auth-oauth-providers.md),
> which is frontend-neutral: read it when you pick a real provider.

**Before any code** (every build):

<!-- generated:start always front-door=web-app -->
- `python/references/patterns-common-gotchas.md` — The consolidated trip list: line-based `.rbtrc`, `--application-name`, no `__init__.py`, kwargs not Request wrappers, `self.ref().state_id`, zero defaults, `MixedContextsError`, the auto-constructed `User`.
<!-- generated:end -->

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
- `python/references/lifecycle-project-setup.md` — Canonical layout, `pyproject.toml`, the required `.gitignore` and project-root `.mypy.ini` (without it type-checking is useless), no `__init__.py` anywhere, generated code under `backend/`.
- `python/references/lifecycle-rbtrc.md` — `.rbtrc` is line-based `<subcommand> <flag>`, not YAML; `--application-name` (not `--name`) persists state; `--env-file` for secrets; `serve run` lines for production; named configs.
- `python/references/lifecycle-secrets.md` — only when the app needs secrets (API keys, OAuth client secrets).
<!-- generated:end -->

**Before the servicer:**

<!-- generated:start reading-list front-door=web-app step=servicer -->
- `python/references/lifecycle-initialize-hook.md` — Each `initialize` call runs once in the app's lifetime, not per boot, so a migration needs a new alias; create singletons here, not in `__init__`; failures retry forever.
- `python/references/rpc-calls.md` — Pass kwargs, never a Request wrapper: `await ref.deposit(context, amount=10)`; the context type must match the method; constructors return `(ref, response)`; `asyncio.gather` for concurrency.
- `python/references/servicer-constructor.md` — Set initial state in the constructor method, branching on `context.constructor`, never in `__init__`; callers use `Service.create`; calling constructors from `initialize` and from a Transaction.
- `python/references/servicer-reader.md` — The reader signature must match the API file; never mutate `self.state`; readers run concurrently and may call other actors, read-only.
- `python/references/servicer-writer.md` — A writer mutates `self.state` on one actor only, never calling another actor's writer; errors roll back the mutation; writers may return no response.
- `python/references/rpc-constructor-calls.md` — Call constructors as `<X>.create(context, id, ...)` or `<X>.<Ctor>(...)`, never `<X>.ref(id).<ctor>(...)`, which skips creation semantics; `create` is idempotent; reuse the returned ref.
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

**Before the authorizers** (browser users — see "Auth in Web Apps"
above for the dev-vs-prod sequence):

<!-- generated:start reading-list front-door=web-app step=auth -->
- `python/references/auth-allow-deny.md` — `allow()` only for genuinely public endpoints, never to silence dev auth warnings or for "internal-only" methods; `deny()` locks a method out; return an instance; one authorizer per servicer.
- `python/references/auth-allow-if.md` — `allow_if(all=[...])` or `allow_if(any=[...])`, never both; `all` evaluates in order and short-circuits, so cheap predicates go first; how the decisions aggregate.
- `python/references/auth-built-in-predicates.md` — `has_verified_token`, `is_app_internal` and `state_id_is_user_id` and their common compositions; a self-scheduled workflow needs `is_app_internal`; predicates always take `**kwargs`.
- `python/references/servicer-authorizer.md` — Write real rules on every servicer before the first test; list the tokenless call paths first; identity does not cross servicer calls; `oauth=` vs. the `token_verifier=` escape hatch.
- `python/references/auth-custom-predicates.md` — Keyword-only predicates ending in `**kwargs`, annotated or `mypy` fails; sync or async; order by cost in `all`; return `PermissionDenied` vs. `Unauthenticated` correctly; per-method rules.
- `python/references/auth-external-api-calls.md` — only when calling an external service's API as the user.
- `mcp-ui/references/auth-oauth-providers.md` — only when you pick a real (production) provider.
- `python/references/stdlib-oauth-tokens.md` — only when storing a user's OAuth tokens for an external service.
- `python/references/auth-claims.md` — only when you use claims or `set_claims`.
<!-- generated:end -->

**Before the frontend:**

<!-- generated:start reading-list front-door=web-app step=frontend -->
- `references/react-client.md` — Set `VITE_REBOOT_URL` in dev: the default resolves to Vite's origin, not the backend. Also the `web/` Vite shell (`server.host`), sign-in/out, accessible markup, and showing typed errors.
- `python/references/react-generated-client.md` — What `rbt generate --react=` emits: `use<Type>()` overloads, three-field reader returns, mutations resolving to `{ response, aborted }` instead of throwing, typed errors, snake-to-camel naming.
<!-- generated:end -->

**Before the tests:**

<!-- generated:start reading-list front-door=web-app step=tests -->
- `python/references/patterns-idempotency.md` — What `IdempotencyUncertainError` means and when a retry needs an idempotency key; idempotent `create` / `initialize` calls, `context.constructor` for set-once fields, UUIDv7 for insertable records.
- `python/references/testing-features.md` — The built-in steps' exact spelling (who calls, `creates` / `does`, saved values, `eventually`, aborts, tasks), `@wip` / `@blocked`, feature / rule / scenario shape, custom steps, mocks.
- `python/references/testing-project-setup.md` — `tests/` layout, `pytest.ini` with three paths so generated `_rbt` modules import, `reboot[dev]` dev-deps, git-ignored recordings, `uv run pytest`; never construct servicers directly.
- `python/references/testing-web-app.md` — The `frontend` fixture and web app steps, sign-in clicked through then bound, recordings, and the accessible markup (paired labels, named buttons, captioned tables) a page needs to be driven.
- `python/references/testing-external-context.md` — only when writing custom steps or harness tests.
- `python/references/testing-failure-recovery.md` — only when the app has a spawned task, a `Workflow`, or scheduled work.
- `python/references/testing-harness.md` — only when writing custom steps.
<!-- generated:end -->

The order of work around the feature files (agree in English, tag
`@wip`, iterate on scenarios) is the [`feature` skill](../feature/SKILL.md).

**Before running the app:** the [`run` skill](../run/SKILL.md).

If you find yourself grepping the framework's installed source or a
generated file to answer a question, the next section is for you —
do not explore it in the main conversation.

## Never Read Generated or Installed Source in the Main Thread

`*_rbt.py`, `*_rbt_react.ts`, `site-packages/`, `node_modules/`,
and codegen templates run to tens of thousands of lines. Every one
you open is re-sent on every remaining turn, which makes reading
them the most expensive way in the system to learn a fact.

The generated surfaces you actually need are written out in these
references — the React client in
[`references/react-client.md`](references/react-client.md), the
backend shapes in `python/references/`. Use them.

If something genuinely isn't covered, bound the output hard: a
targeted `grep -n … | head -40`, or `sed -n '<start>,<end>p'` over
a known range. Never a whole generated file, never an unbounded
recursive grep.

## Workflow: Settle the Design, Then Build

**Always settle the design before writing code.** The state model
is the foundation — getting entities, field types, or method types
wrong means regenerating everything across the project.

### Design Phase

0. For each capability the app has, follow the
   [`feature` skill](../feature/SKILL.md): agree on it in plain
   English with the user, and write it down as a `@wip` feature
   file before the API exists. The design below is derived from
   those features.
1. Analyze the user's description using the State Model Assessment
   below.
2. State the design you are about to build:
   - Application types: state shape (fields, types, tags).
   - Method map: which operations, which method type
     (Reader/Writer/Transaction/Workflow).
   - Route surface: which pages does the SPA need; which methods
     each page calls.
   - Auth: anonymous, logged-in, or per-user state? If per-user,
     declare a `User` type for owned data and route through it.
3. Then execute the Step-by-Step Build Flow.

For updates to existing apps, still work the design first: read
current state, state the changes, then modify.

### Writing the Design for a Human Reader

The design is read by a **human who has not read the skill files**.
They are judging the design — entities, collections, methods,
routes, auth — not verifying that you followed the skill. Write
so it stands on its own.

**Don't quote skill-internal terms** when presenting the design.
They mean nothing outside this skill:

- `Shape A` / `Shape B` / `Shape C` — name the actual data
  structure: `list[Sub]` of inline sub-records, `list[str]` of
  foreign state IDs, `OrderedMap` of foreign state IDs.
- "non-state `Model`" — say "a flat sub-record that lives and
  dies with the parent" or "no identity of its own", in domain
  terms.
- Filenames like `state-collections.md` / `api-pydantic.md` —
  drop the citation; if the rule matters to the design, explain
  it inline.
- `factory=True`, `Field(tag=N)`, raw pydantic spellings — fine
  to mention briefly when the spelling itself is the design
  decision, but never as the explanation.

**For every design choice, give the what + the why.** The _what_
is the concrete data structure, method type, or route. The _why_
is a one-clause reason rooted in the user's domain ("grows
without bound, so we need pagination"; "no methods or auth of
its own, so it lives inline"; "logged-in users only, because the
document is per-account").

**Examples.**

Collection shape — BAD:

> `documents_index_id: str` — ID of an OrderedMap actor that
> holds this user's Documents (Shape C from
> state-collections.md — unbounded).

Collection shape — GOOD:

> `documents_index_id: str` — points to an OrderedMap that
> holds this user's Documents. An OrderedMap (rather than an
> inline list) because the document collection grows without
> bound and the dashboard will paginate / sort by recency.

Nested model — BAD:

> Comment and Revision are non-state Models — Shape A.

Nested model — GOOD:

> Comment and Revision live inline on Document as
> `list[Comment]` / `list[Revision]`. They don't get their own
> state actors because they have no lifecycle, methods, or auth
> independent of the Document they belong to.

**Escape hatch.** When the precise type name _is_ what the reader
needs to see ("I'm proposing `OrderedMap` here, not `list[str]`"),
name the type — but pair it with the plain-English reason in the
same sentence. The rule is "no bare jargon", not "no technical
terms".

## State Model Assessment

Before writing code, analyze the user's request:

1. **Application types — decompose aggressively.** List every
   distinct entity the user is going to add / edit / list / find
   over time (todos, documents, posts, accounts, people, …).
   **Each entity becomes its own `Type` with its own state**, even
   when "each user only has a few of them". Anything you can
   imagine being `add`-ed / `remove`-d / `find`-ed by name has its
   own identity and belongs in its own actor. The default wrong
   move is packing everything into one parent's state as
   `list[Todo]` (or `list[Document]`, `list[Post]`, …) — that
   flattens N actors into one, prevents per-entity auth/methods,
   and forces a full rewrite when the collection grows. See
   `python/references/state-collections.md` Step 1 for the full
   decomposition signal list. Reading those actors back onto one
   page is `python/references/patterns-cross-actor-reads.md`.
2. **Per-user state?** If yes, declare a `User` type and route
   creation through it the same way `mcp-ui` does — the
   `User`-front-door pattern is independent of MCP. If the app is
   anonymous or all users share state, skip `User`.
3. **Container shape for each collection.** Once an entity is its
   own `Type`, parents store **references**, not objects. Three
   shapes (full table + worked example in
   `python/references/state-collections.md`):
   - `list[Sub]` of non-state `Model`s — bounded sub-records with
     no identity of their own (line items on an Order, tags on a
     Post). NOT for entity collections.
   - `list[str]` of foreign state IDs — bounded entity collection
     (low hundreds, occasionally low thousands) you always read
     whole.
   - `OrderedMap` of foreign state IDs — collection grows without
     bound, needs pagination / range queries / ordered iteration.
     The default choice for any "list of things the user keeps
     adding to".
4. **State shape (per type)**: Fields, types — lists, nested
   objects, primitives. Each gets `Field(tag=N)`. Nested `Model`
   sub-objects owned 1:1 by a parent state must be
   `Optional[X] = Field(tag=N, default=None)` and hydrated in the
   parent's factory `create` Writer; non-Optional `Model`-typed
   fields reject `default=` / `default_factory=`. Full rules in
   `python/references/api-pydantic.md`.
5. **Operations**: Map to the right method type:
   - `Reader` — read-only queries.
   - `Writer` — single-state mutations.
   - `Transaction` — multi-state atomic operations.
   - `Workflow` — long-running control flows with loops, scheduling,
     and idempotency helpers.
6. **Pages / routes**: Which SPA routes exist? Which methods does
   each page call? React hooks generated by `rbt generate --react=...`
   wrap the calls.
7. **Auth**: Anonymous-only, public-read + authed-write, fully
   locked down, …? See `python/references/auth-*.md`.

## Project Layout

```
<project-root>/
├── .python-version
├── .rbtrc
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
    ├── index.html
    └── src/
        ├── main.tsx         # RebootClientProvider entry
        ├── App.tsx          # Routes + top-level component
        ├── pages/
        │   └── <page>.tsx
        └── api/             # Generated TypeScript client
                             # (output of `rbt generate --react=`)
```

Key differences from a `mcp-ui` layout:

- `web/index.html` lives at the top of `web/` (single SPA entry),
  **not** under `frontend/mcp/<name>/index.html`.
- `vite.config.ts` is the **stock** Vite config — no nested-output
  override, no `viteSingleFile` plugin. There's no MCP host
  resolving artifacts by path.
- No MCPJam inspector.

## Step-by-Step Build Flow

**All commands run from the application directory.**

1. Create `.python-version`, `pyproject.toml`, `.rbtrc`, and
   `.mypy.ini` — same shape as in
   `python/references/lifecycle-{project-setup,rbtrc}.md`. In
   `.rbtrc`, point the React codegen at `web/src/api`:
   ```sh
   generate --react=web/src/api
   generate --web=web/src/api
   ```
2. `uv sync`.
3. Start the developer dashboard — load the
   [`dashboard` skill](../dashboard/SKILL.md) and follow it — so
   the user can watch the API take shape while you write it. If it
   fails to come up, say so in one sentence and keep building; do
   not stop to debug it.
4. Write the API definition (`api/<pkg>/v1/<name>.py`). Pydantic
   rules live in `python/references/api-pydantic.md`; method
   marker → context-type rules in
   `python/references/api-methods.md`. Do **not** add `mcp=Tool()`
   or `UI()` — those are MCP-UI only.
5. `uv run rbt generate`. Don't read what it wrote: the signature
   your servicer must match is in `python/references/api-methods.md`
   ("The Servicer Signature Each Declaration Obliges").
6. Write the servicer (`backend/src/servicers/<name>.py`) —
   context-type patterns in `python/references/servicer-*.md`.
7. Write `main.py` — `python/references/lifecycle-application-entry.md`.
8. Initialize the React app at `web/` with your preferred tool
   (e.g. `npm create vite@latest web -- --template react-ts`) or
   a Reboot-provided template if one exists for plain web apps.
   Read [`references/react-client.md`](references/react-client.md)
   now — it has the `package.json` dependency set, the `dedupe`
   entry the Vite config needs, and `web/.env.development` with
   `VITE_REBOOT_URL`.
9. `cd web && npm install` and add the Reboot React client
   package(s) per your project's `package.json`.
10. `uv run rbt generate` again — the React bindings need
    `node_modules` to resolve types correctly.
11. Build the frontend from
    [`references/react-client.md`](references/react-client.md): the
    provider and its `url`, the generated hook/mutator/error
    declarations, sign-in, and typed errors are all written out
    there. Write the calls from that reference and do **not** open
    `web/src/api/**/*_rbt_react.ts` to check them — it is tens of
    thousands of lines that then ride along on every later turn.
12. `cd web && npm run build` (sanity check the bundle).
13. **Write and run the scenarios of every feature before handing
    the app off.** Each feature file from the design phase gets its
    scenarios now: every action the user should be able to _do_ in
    the UI ("sign up and see my profile", "submit the form and see
    the result", "delete an item and have it disappear") is a
    scenario in the built-in steps of
    `python/references/testing-features.md`, and the flows a person
    clicks through are web app scenarios per
    `python/references/testing-web-app.md` (they need `playwright`,
    `pytest-playwright`, `uv run playwright install chromium`, and
    the page's accessible markup from step 11). Every step names
    who calls; a user who must be signed in is declared with
    `"alice" is an authenticated user`, which is how the real
    authorizers get exercised: register the **real** servicers and
    never subclass one to weaken its `authorizer()`. Let factories
    make ids up. Tag what cannot pass yet `@blocked` with its
    reason; leave `@wip` where work continues. When a scenario
    fails for a reason that looks like it is inside the framework,
    check `python/references/patterns-idempotency.md` and
    `patterns-common-gotchas.md` before reading `site-packages`.
    Run `uv run pytest` and fix anything that fails.
    Then type-check: run `uv run mypy backend/ tests/` from the project
    root and fix every error (config and rationale in
    `python/references/lifecycle-project-setup.md`). Do not
    proceed to the next step until every scenario passes (or is
    `@blocked` with a reason) and mypy is green — together they
    are what catches contract bugs before the user opens the
    browser. Point the user at the dashboard's Features page to
    review the features, and at the recordings of the browser
    scenarios.
14. Run the app — load the [`run` skill](../run/SKILL.md) and
    follow it. It is the single canonical "start the app"
    procedure: it makes sure dependencies and secrets are in
    place, starts the backend and frontend dev server, waits for
    them to come up, and hands the user the URLs plus a first page
    to open.

## Update Flow

When modifying an existing app:

1. Read `.rbtrc`, the API definition, servicer, `main.py`, and
   `web/src/App.tsx`.
2. Assess state model changes. If the app has persisted state or
   has been deployed, read
   `python/references/api-schema-evolution.md` to understand the
   rules you must follow for API schema evolution.
3. Agree on the changed or new feature in English and write it
   down first, per the [`feature` skill](../feature/SKILL.md):
   the feature file, tagged `@wip`, before the API changes.
4. Update the API definition (every new property with a
   `description=`) → re-run `uv run rbt generate`.
5. Update servicer methods.
6. Update React components and routes, keeping the markup
   accessible (labels paired with inputs, buttons that say what
   they do) so scenarios can drive the new page.
7. Update the scenarios: the feature file's, and a web app
   scenario for a flow a person clicks through. Re-verify the
   backend: run `uv run mypy backend/ tests/` from the project root and
   `uv run pytest`; fix every error and failure
   before handing back, and ask before removing `@wip`.
8. If the app isn't already running, bring it up with the
   [`run` skill](../run/SKILL.md). If it is already running under
   `rbt dev run`, the `--watch` globs reload it automatically — no
   restart needed. Editing `.env` likewise triggers a restart, so
   a new or changed secret is re-read by `--env-file` without a
   manual relaunch.

Specific patterns and file shapes live in the `python` skill's
references and the table above — read them on demand based on
what's changing.
