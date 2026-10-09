---
name: mcp-ui
description: Build complete Reboot MCP UIs for ChatGPT, Claude, VSCode, Goose, and other MCP hosts. Layers on top of the python skill for backend mechanics; covers what's specific to MCP UIs — the User-type front door, MCP tool exposure, the UI() method type, and the full React/Vite scaffolding.
argument-hint: [<app-description>]
allowed-tools: Bash, Read, Write, Glob, Grep, Edit
---

# mcp-ui — Build Reboot MCP UIs

> **Version notices:** if `rbt` reports a version mismatch or a newer
> Reboot, follow the [upgrade skill](../upgrade/SKILL.md).

An MCP UI is one of a Reboot app's two **front doors** (the ways people
reach its backend; [`app` skill](../app/SKILL.md)): tools and views
inside an AI chat app such as Claude or ChatGPT.

**Follow [`../build/SKILL.md`](../build/SKILL.md)** (design phase, state
model assessment, build steps, update flow). This skill holds the MCP UI
differences: the `User`-type front door, `mcp=`, `UI()`, `oauth=`
provider selection, example prompts, nested `frontend/mcp/<name>/`
bundles, the setup wizard and MCPJam, and each step's reading list.
A dual-frontend app (MCP plus a browser SPA, one backend) also loads the
[`web-app` skill](../web-app/SKILL.md); see the
[`app` skill](../app/SKILL.md) for what they share.

Install: `curl -fsSL https://reboot.dev/install.sh | bash`, then
restart the agent.

## When to Use

- Building or changing a Reboot MCP UI.
- Running an existing one needs no design or build: load the
  [`run` skill](../run/SKILL.md). State survives restarts because
  `.rbtrc` has `dev run --application-name=<name>`.

## Key Concepts (MCP UI–specific)

### `User` and Application Types

- **`User`** is the AI's front door for **creating and locating**
  application-type instances, not a container for all state: it holds
  identity and the **IDs** of what it owns; its methods are
  `Transaction`s that create instances and `Reader`s that locate IDs
  (directly or via indexes). `User`-scoped UIs (a dashboard over the
  whole user, a global browser) live here.
- **Application types** (`Counter`, `Person`, `Task`) hold entity state,
  constructed by a `create` Writer with `factory=True`
  (`python/references/servicer-constructor.md`). **Everything specific
  to an existing entity — Readers, Writers, UIs — lives on its own
  `Type`**, never on `User`: the AI passes the entity ID to the tool,
  and the generated `use<Type>()` hook resolves it with no arguments.

**UI Placement.** Per-entity UIs (`show_person`, `edit_task`) go on the
entity's `Type` with `request=None`; only UIs about the user as a whole
go on `User`. The most common scaffolding mistake is a per-entity UI on
`User` with the ID in a `request=<Model>` field
(`references/api-method-types.md`, "UI Placement"). The second is `User`
accreting unrelated concerns (auth/session, persona, background-engine
config, a UI cache): writers on one actor serialize, so a login contends
with a persona edit — split each into its own `Type`
(`python/references/state-actor-decomposition.md`). The `UserServicer`
+ `<X>.create(context)` pattern: `references/servicer-patterns.md`.

### Tool Exposure — `mcp=`

Every method declares its exposure explicitly, all in the API file (no
`@mcp.tool()` decorators):

- **`mcp=Tool()`** — AI-callable; required on every method the AI
  should call, `User` methods included.
- **`mcp=None`** — hidden from the AI (human-only actions, or to cut
  context bloat).
- **`Tool(name="...", title="...")`** — its only fields in 1.6.0. No
  MCP annotations (`readOnlyHint`, …), so hosts such as Claude ask
  permission before every call, `Reader`s included; "Always allow" is
  per tool, with no app-side workaround.

### `UI()` and the Method Types

`Reader` / `Writer` / `Transaction` / `Workflow` are as in
`python/references/api-methods.md`. MCP UIs add **`UI()`**: opens a
React UI in the MCP client. Takes `request=` (a config `Model` or
`None`; a `Model`'s fields become component props), `path=` (web dir
relative to the project root), `title=`, `description=`. **No servicer
implementation** — the React app _is_ the implementation.

### Auth — `oauth=` Provider Selection

Providers, rules before the first test, the `User` default rule and
`allowed_origins` are build Step 4. MCP-specific:

- The `oauth=` principal **is** the user, with no middle ground: every
  user signs in through this OAuth flow, or the app has no per-user auth.
- Providers, the `/__/oauth/callback` URL, switching costs:
  `references/auth-oauth-providers.md`; none fits (self-hosted
  Keycloak, internal SSO): `references/auth-custom-oauth-provider.md`.
- **Acting as the user at the provider:** `Google` / `GitHub` / `Auth0`
  accept extra `scopes=[...]` and `store_tokens=True` (with `Auth0`, an
  Auth0 token, not the upstream Google one). Tokens are stored
  encrypted, read with
  `OAuthTokenManager.ref(GOOGLE).fetch(context, user_id=context.state_id)`;
  make the outbound call inside a `Workflow`. Shortcut:
  `references/auth-store-tokens.md`; full recipe:
  `python/references/auth-external-api-calls.md`.

### Example Prompts (Root-Page Wizard)

Every MCP UI ships **example prompts** (required): named chat scenarios
the root-page wizard offers a fresh user.

- `ExamplePrompt(title=..., prompts=[...])` from `reboot.application`:
  `title` is a short label and identity key (same title replaces an
  entry); `prompts` is an **ordered sequence**, one message per turn,
  walking a real flow (create → act → view).
- Write ~3 covering the main user stories, phrased as a real user talks.
- **Show the UI**: each ends on (or passes through) a "show me / open /
  view …" turn that makes the AI pick a `UI()` tool (the counter's
  "…and show me the counter"); every `UI()` method is reached by at
  least one.
- Put them in `backend/src/example_prompts.py`, passed to
  `Application(example_prompts=...)`; shapes and a worked set in
  `references/project-shell.md` (`mcp-ui-counter` is canonical).

### Setup Wizard and MCPJam

Hand off the **setup wizard at the backend root
(`http://localhost:9991`)**, not the `/mcp` URL: it connects an MCP
client (Claude, ChatGPT, MCPJam, …) and completes OAuth. Surface and open
it once at first startup, as the `run` skill directs. Never start the
MCPJam inspector yourself — the wizard launches it on demand. Bare
`rbt dev run` / `npm run dev` print only the API/MCP/inspect URLs, not
the wizard.

## Project Structure

```
<project>/
├── .python-version
├── .rbtrc                   # Line-based config (NOT YAML!)
├── .mypy.ini                # Type-check config (python skill)
├── pyproject.toml           # Python deps (uv)
├── pytest.ini               # testpaths: tests; pythonpath: backend/src backend/api api
├── api/
│   └── <pkg>/v1/
│       └── <name>.py        # API definition
├── backend/
│   └── src/
│       ├── main.py          # Application entrypoint
│       ├── example_prompts.py  # Wizard example prompts
│       └── servicers/
│           └── <name>.py    # Servicer implementation
├── tests/
│   ├── <capability>.feature  # One feature per capability
│   └── <name>_test.py       # `application` fixture + `scenarios(...)`
└── frontend/
    ├── package.json
    ├── build.mjs            # Discovers + builds every UI
    ├── tsconfig.json
    ├── tsconfig.app.json
    ├── tsconfig.node.json
    ├── vite.config.ts       # Nested output: dist/mcp/<name>/index.html
    ├── api/                 # Generated React bindings (rbt generate)
    ├── mcp/
    │   └── <ui-name>/
    │       ├── index.html
    │       ├── index.css        # Theme variables
    │       ├── main.tsx         # RebootClientProvider entry
    │       ├── App.tsx          # React component
    │       └── App.module.css
    └── web/                 # Optional standalone browser SPA
        ├── index.html
        └── src/
            ├── main.tsx
            └── App.tsx
```

Starting files: `../build/templates/mcp-ui/`. Each UI builds to
`frontend/dist/mcp/<ui-name>/index.html`, where the host discovers it;
flattening that output breaks discovery.

## Which References to Read, and When

One group per step of [`../build/SKILL.md`](../build/SKILL.md): backend
mechanics from the `python` skill's references, the MCP UI shape from
this skill's `references/`. Read each at its step, once, one per tool
call; each appears in exactly one group. Pattern references
(`patterns-*.md`) are off the build path; read one when its situation
comes up (catalog in the `python` skill).

<!-- The lists below are generated from each reference's frontmatter
by tools/gen-index.py. Edit the frontmatter, not the lists. -->

> **Never read `web-app/references/*` for an MCP UI.** They cover the
> standalone SPA (top-level `web/` Vite shell, `VITE_REBOOT_URL`,
> `<RebootClientProvider>`, browser sign-in buttons), not the nested
> `frontend/mcp/<name>/` bundles an MCP host loads. Use
> [`references/react-scaffolding.md`](references/react-scaffolding.md)
> and [`references/react-app-tsx.md`](references/react-app-tsx.md).

**Before the API definition:**

<!-- generated:start reading-list front-door=mcp-ui step=api -->
- `references/api-method-types.md` — Every method needs `mcp=Tool()` or `mcp=None`; an entity's `UI()` goes on its Type, not `User`; `factory=True` `create`.
- `python/references/api-methods.md` — The factory fixes the servicer's context type, and `mcp=` is required; `Reader`/`Writer`/`Transaction`/`Workflow`, `factory=True`, `errors=`, `description=`.
- `python/references/api-pydantic.md` — A non-zero `Field` default is rejected at import; tags, zero defaults, `API(...)` wiring, Request/Response naming.
- `references/api-state-shapes.md` — Never nest state Models; `list[Item]` only for bounded identity-less sub-records; a nested `Model` is `Optional`, hydrated in `create`.
- `python/references/state-actor-decomposition.md` — A Type with unrelated field clusters serializes writers and grows a God `User`; split it into separate Types.
- `python/references/state-collections.md` — Never `list[Entity]` on parents; decide if each item is its own Type, then `list[Sub]`, ID list or `OrderedMap`.
- `python/references/state-nested-models.md` — Never a state `Model` inside another; group related fields in nested non-state `Model`s, mutated in place.
- `python/references/api-schema-evolution.md` — only when changing an API that is deployed or has persisted state.
- `python/references/api-errors.md` — only when the API declares typed errors.
- `python/references/state-scalar-fields.md` — only when a field holds a secret, token or PII, or you want a non-zero default.
<!-- generated:end -->

**Before the project shell** (`.python-version`, `pyproject.toml`,
`.rbtrc`, `.mypy.ini`, `main.py`):

<!-- generated:start reading-list front-door=mcp-ui step=shell -->
- `python/references/lifecycle-application-entry.md` — Pass servicer classes, not instances, and register stdlib libraries; `async def main()` awaiting `Application(servicers=[...], initialize=...).run()`.
- `python/references/lifecycle-project-setup.md` — Never add `__init__.py` or edit `*_rbt.py`; copy `build/templates/<front-door>/`; mypy sees `self.state` as `Any`: typed locals.
- `python/references/lifecycle-rbtrc.md` — `.rbtrc` is line-based, not YAML; `--application-name` not `--name`; `--env-file` for secrets; `serve run` lines; named configs.
- `references/project-shell.md` — Dropping `oauth=` fails startup; copy `build/templates/mcp-ui/`: `.rbtrc` with `--default-config=hmr`, `:hmr`/`:dist` configs, `example_prompts=`.
- `python/references/lifecycle-secrets.md` — only when the app needs secrets (API keys, OAuth client secrets).
<!-- generated:end -->

**Before the servicer:**

<!-- generated:start reading-list front-door=mcp-ui step=servicer -->
- `references/servicer-patterns.md` — Never await a workflow from `UserServicer.create_<X>`, `.schedule()` it; the Transaction calls `<X>.create(context)`, returns `state_id`; workflow-body idioms.
- `python/references/lifecycle-initialize-hook.md` — Each `initialize` call runs once per app lifetime, not per boot; migrations need new aliases; failures retry forever.
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
servicer before the first test):

<!-- generated:start reading-list front-door=mcp-ui step=auth -->
- `python/references/auth-allow-deny.md` — `allow()` to silence warnings, pass tests or mark internal methods makes them public; `deny()` blocks everyone; `return allow()`.
- `python/references/auth-allow-if.md` — `is_app_internal` in `any` turns anonymous `Unauthenticated` into `PermissionDenied`; `allow_if(all=[...])` or `allow_if(any=[...])`, never both or nested; `all` short-circuits.
- `python/references/auth-built-in-predicates.md` — Token predicates alone deny servicer-to-servicer calls; `has_verified_token`, `is_app_internal`, `state_id_is_user_id` and compositions.
- `references/auth-oauth-providers.md` — Switching providers later strands user state; `OAuthProviderByEnvironment(dev=Development(), prod=Google(...))`, credentials as secrets, `/__/oauth/callback`.
- `python/references/servicer-authorizer.md` — Without real rules every external call is denied; identity doesn't cross servicer calls; tokenless paths; `oauth=` vs `token_verifier=`.
- `python/references/auth-custom-predicates.md` — Predicates must be keyword-only with `**kwargs` and check `context.app_internal` first; per-method rules via `<Type>.Authorizer(method=rule, _default=rule)`.
- `python/references/auth-external-api-calls.md` — only when calling an external service's API as the user.
- `references/auth-store-tokens.md` — only when the app acts as the user at its own identity provider's API.
- `python/references/stdlib-oauth-tokens.md` — only when storing a user's OAuth tokens for an external service.
- `python/references/auth-claims.md` — only when you use claims or `set_claims`.
- `references/auth-custom-oauth-provider.md` — only when none of the shipped OAuth providers fits.
<!-- generated:end -->

**Before the frontend:**

<!-- generated:start reading-list front-door=mcp-ui step=frontend -->
- `references/react-scaffolding.md` — Flattening `vite.config.ts` output breaks UI discovery at `frontend/dist/mcp/<name>/index.html`; copy `build/templates/mcp-ui/frontend/`; `npm install` before second `rbt generate`.
- `references/react-app-tsx.md` — No-id `use<Type>()` returns `{ <type>, isLoading }`: render a child once the handle exists; `_rbt_react` imports; composing readers.
- `python/references/react-generated-client.md` — Mutations resolve to `{ response, aborted }`, never throw; `rbt generate --react=` output: `use<Type>()` overloads, reader returns, naming.
- `references/ui-design.md` — The web app's principles inside a host: shared `frontend/mcp/styles.css`, `useHostTheme()` (the host owns light/dark), one focused view, skeletons.
- `references/pop-out-to-web-app.md` — only when a widget needs a "pop out into the web app" button.
<!-- generated:end -->

**Before the tests:**

<!-- generated:start reading-list front-door=mcp-ui step=tests -->
- `python/references/patterns-idempotency.md` — Replayed calls return the first run's response; what `IdempotencyUncertainError` means, when retries need keys, idempotent `create`/`initialize`.
- `python/references/testing-features.md` — Built-in steps match their exact spelling; who calls, `creates` / `does`, saved values, `eventually`, aborts, `@wip`, custom steps.
- `python/references/testing-project-setup.md` — Missing `pytest.ini` paths break `_rbt` imports; no `pytest-asyncio`; `tests/` layout, fixture with `allowed_origins=[]`, `reboot[dev]`.
- `python/references/testing-external-context.md` — only when writing custom steps or harness tests.
- `python/references/testing-failure-recovery.md` — only when the app has a spawned task, a `Workflow`, or scheduled work.
- `python/references/testing-harness.md` — only when writing custom steps.
<!-- generated:end -->

Order of work around feature files (agree in English, tag `@wip`,
iterate on scenarios): the [`feature` skill](../feature/SKILL.md).

**Before running the app:** the [`run` skill](../run/SKILL.md).

Grepping installed framework source or a generated file? Stop: see
build's "Never Read Generated or Installed Source in the Main Thread".
