---
name: mcp-ui
description: Build complete Reboot MCP UIs for ChatGPT, Claude, VSCode, Goose, and other MCP hosts. Layers on top of the python skill for backend mechanics; covers what's specific to MCP UIs — the User-type front door, MCP tool exposure, the UI() method type, and the full React/Vite scaffolding.
argument-hint: [<app-description>]
allowed-tools: Bash, Read, Write, Glob, Grep, Edit
---

# mcp-ui — Build Reboot MCP UIs

> **Version notices:** if `rbt` reports a version mismatch or that a
> newer Reboot is available, the [upgrade skill](../upgrade/SKILL.md)
> says how and when to react.

**Follow [`../build/SKILL.md`](../build/SKILL.md)** — the design phase,
state model assessment, build steps and update flow every Reboot app
shares. This skill holds what differs for an MCP UI: the `User`-type
front door, MCP tool exposure (`mcp=`), the `UI()` method type,
`oauth=` provider selection, example prompts, the nested
`frontend/mcp/<name>/` bundles, the setup wizard and MCPJam, and the
reading list for each build step. Backend mechanics are the `python`
skill's references, reached through the lists below. A dual-frontend app (MCP plus a browser SPA, one backend) also
loads the [`web-app` skill](../web-app/SKILL.md); see the
[`app` skill](../app/SKILL.md) for what they share.

Install: `curl -fsSL https://reboot.dev/install.sh | bash`, then
restart the agent.

## When to Use

- Building or changing a Reboot MCP UI.
- Running an existing MCP UI needs no design or build phase: load
  the [`run` skill](../run/SKILL.md). State survives restarts because
  `.rbtrc` has `dev run --application-name=<name>`.

## Key Concepts (MCP UI–specific)

### `User` and Application Types

- **`User`** is the AI's front door for **creating and locating**
  application-type instances — entry point and delegation, not a
  container for all state. It holds identity and the **IDs** of what
  it owns; its methods are `Transaction`s that create instances and
  `Reader`s that locate their IDs (directly or via indexes). `User`-scoped UIs
  (a dashboard over the whole user, a global browser) live here.
- **Application types** (`Counter`, `Person`, `Task`) hold the entity
  state and are constructed by a `create` Writer with `factory=True`
  (the MCP UI spelling of a constructor; mechanics in
  `python/references/servicer-constructor.md`). **Once an entity
  exists, everything specific to it — Readers, Writers, UIs — lives on
  its own `Type`**, never on `User`: the AI passes the entity ID to the
  tool, and the generated `use<Type>()` hook resolves the same ID with
  no arguments.

**UI Placement.** Ask of each UI: is the AI passing in an entity ID,
or is the UI about the user as a whole? Per-entity UIs (`show_person`,
`edit_task`) go on the entity's `Type` with `request=None`; putting
one on `User` with the ID in a `request=<Model>` field is the most
common scaffolding mistake (`references/api-method-types.md`, "UI
Placement"). The second most common is letting `User` accrete
unrelated concerns (auth/session, persona, background-engine config, a
UI cache) — writers on one actor serialize, so a login contends with a
persona edit; split each into its own `Type`
(`python/references/state-actor-decomposition.md`). The `UserServicer`
+ `<X>.create(context)` pattern is in `references/servicer-patterns.md`.

### Tool Exposure — `mcp=`

Every method declares its MCP exposure explicitly:

- **`mcp=Tool()`** — an AI-callable tool. Required on every method,
  `User` methods included, that the AI should call.
- **`mcp=None`** — hidden from the AI: human-only actions, or to cut
  context bloat.
- **`Tool(name="...", title="...")`** — override the tool name or add
  a human-readable title — its only fields in 1.6.0. Tools carry no
  MCP annotations (`readOnlyHint`, …), so a host such as Claude asks
  permission before every call, `Reader`s included; "Always allow" is
  per tool and there is no app-side workaround.

All MCP surface is declared in the API file — no `@mcp.tool()`
decorators.

### `UI()` and the Method Types

`Reader` / `Writer` / `Transaction` / `Workflow` behave exactly as
`python/references/api-methods.md` describes. The MCP UI adds:

- **`UI()`** — opens a React UI inside the MCP client. Takes
  `request=` (a config `Model` or `None`), `path=` (web dir relative to
  the project root), `title=`, `description=`. **No servicer
  implementation** — the React app _is_ the implementation. When
  `request=` is a `Model`, its fields become props on the component.

### Auth — `oauth=` Provider Selection

Providers, rules before the first test, the `User` default rule and
`allowed_origins` are build Step 4. Specific to MCP UIs:

- In an MCP app the `oauth=` principal **is** the user, and there is
  no middle ground: either every user signs in through this OAuth
  flow, or the app has no per-user auth at all.
- Provider details, the `/__/oauth/callback` URL and switching costs:
  `references/auth-oauth-providers.md`; no shipped provider fits
  (self-hosted Keycloak, internal SSO): `references/auth-custom-oauth-provider.md`.
- **Acting as the user at the provider.** `Google` / `GitHub` /
  `Auth0` can request extra `scopes=[...]` and capture the provider's
  own tokens (`store_tokens=True` — with `Auth0`, an Auth0 token, not
  the upstream Google one). They are stored encrypted, read back with
  `OAuthTokenManager.ref(GOOGLE).fetch(context, user_id=context.state_id)`,
  and the outbound call goes inside a `Workflow`. Shortcut:
  `references/auth-store-tokens.md`; full recipe:
  `python/references/auth-external-api-calls.md`.

### Example Prompts (Root-Page Wizard)

Every MCP UI ships **example prompts** — the named chat scenarios the
root-page wizard offers so a fresh user has something to click the
moment the app boots. Not optional.

`ExamplePrompt(title=..., prompts=[...])` from `reboot.application`:
`title` is a short label and the identity key (same title replaces an
entry); `prompts` is an **ordered sequence** of messages sent one per
turn, walking a real flow through the tools (create → act → view).
Write ~3 covering the main user stories, phrased as a real user talks.
**Make them show the UI**: the `UI()` components are why this is an
MCP **App**, so each example ends on (or passes through) a natural
"show me / open / view …" turn that makes the AI pick a `UI()` tool —
like the counter example's "…and show me the counter" — and every
`UI()` method is reached by at least one example. They live in
`backend/src/example_prompts.py`, passed to
`Application(example_prompts=...)`; shapes and a worked set in
`references/project-shell.md` (`mcp-ui-counter` is canonical).

### Setup Wizard and MCPJam

The handoff is the **setup wizard at the backend root
(`http://localhost:9991`)**, not the `/mcp` URL: it connects an MCP
client (Claude, ChatGPT, MCPJam, …) and completes OAuth. Surface it and
open it once at first startup, as the `run` skill directs. Do **not**
start the MCPJam inspector yourself — it launches on demand from the
wizard. Bare `rbt dev run` / `npm run dev` print only the
API/MCP/inspect URLs and drop the wizard hint.

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

Each group below is what to read at one step of the build flow in
[`../build/SKILL.md`](../build/SKILL.md). The backend mechanics live in
the `python` skill's references; the MCP-UI-specific shape on top of
them lives in this skill's own `references/`.

Read each at its step, once, one per tool call; each reference
appears in exactly one group. Pattern references (`patterns-*.md`)
are off the build path; read one when its situation comes up
(catalog in the `python` skill).

<!-- The lists below are generated from each reference's frontmatter
by tools/gen-index.py. Edit the frontmatter, not the lists. -->

> **Never read `web-app/references/*` for an MCP UI.** They cover
> the standalone browser SPA — a top-level `web/` Vite shell, the
> `VITE_REBOOT_URL` backend URL, `<RebootClientProvider>`,
> browser sign-in buttons — none of which apply to the nested
> `frontend/mcp/<name>/` bundles an MCP host loads. The MCP UI
> equivalents are
> [`references/react-scaffolding.md`](references/react-scaffolding.md)
> and [`references/react-app-tsx.md`](references/react-app-tsx.md).

**Before the API definition:**

<!-- generated:start reading-list front-door=mcp-ui step=api -->
- `references/api-method-types.md` — Every method, `Workflow` included, needs explicit `mcp=Tool()` or `mcp=None`; put an entity's `UI()` on that entity's Type, never on `User` with an ID in `request=`; `factory=True` on `create`.
- `python/references/api-methods.md` — Which factory (`Reader`, `Writer`, `Transaction`, `Workflow`) and the servicer signature and context type each obliges; `factory=True` marks creation; `errors=`, `description=` and the required `mcp=`.
- `python/references/api-pydantic.md` — Every `Field` needs a tag and a zero-value default (non-zero is rejected at import time); wire declarations through `API(...)`; generated Request/Response names come from the method name, not the class.
- `references/api-state-shapes.md` — `list[Item]` only for bounded sub-records without identity, with index-checked CRUD Writers; a single nested `Model` is `Optional` and hydrated in factory `create`; never nest state Models.
- `python/references/state-actor-decomposition.md` — Split a Type whose fields cluster by unrelated concern (auth, persona, background engine, cache) into separate Types, or its writers serialize and `User` becomes a God actor.
- `python/references/state-collections.md` — Decide whether each "list of X" item is its own state Type (usually yes), then pick `list[Sub]`, `list[str]` of IDs, or an `OrderedMap`; never `list[Entity]` on a parent.
- `python/references/state-nested-models.md` — Group related fields into nested non-state `Model`s instead of parallel flat names, and mutate them in place; never put a state `Model` inside another state `Model`.
- `python/references/api-schema-evolution.md` — only when changing an API that is deployed or has persisted state.
- `python/references/api-errors.md` — only when the API declares typed errors.
- `python/references/state-scalar-fields.md` — only when a field holds a secret, token or PII, or you want a non-zero default.
<!-- generated:end -->

**Before the project shell** (`.python-version`, `pyproject.toml`,
`.rbtrc`, `.mypy.ini`, `main.py`):

<!-- generated:start reading-list front-door=mcp-ui step=shell -->
- `python/references/lifecycle-application-entry.md` — An `async def main()` that awaits `Application(servicers=[...], initialize=...).run()`; pass servicer classes, not instances; register stdlib libraries alongside your servicers.
- `python/references/lifecycle-project-setup.md` — Copy `build/templates/<front-door>/`: layout, `pyproject.toml`, `.gitignore`, `.mypy.ini`. No `__init__.py`; never edit `*_rbt.py`; mypy sees `self.state` as `Any` — use typed locals.
- `python/references/lifecycle-rbtrc.md` — `.rbtrc` is line-based `<subcommand> <flag>`, not YAML; `--application-name` (not `--name`) persists state; `--env-file` for secrets; `serve run` lines for production; named configs.
- `references/project-shell.md` — Copy `build/templates/mcp-ui/`: `.rbtrc` with `--default-config=hmr` and `:hmr`/`:dist` configs, no `--react-extensions`; `main.py` with `oauth=` and `example_prompts=`.
- `python/references/lifecycle-secrets.md` — only when the app needs secrets (API keys, OAuth client secrets).
<!-- generated:end -->

**Before the servicer:**

<!-- generated:start reading-list front-door=mcp-ui step=servicer -->
- `references/servicer-patterns.md` — `UserServicer.create_<X>` Transaction calls `<X>.create(context)` and returns `state_id`; `.schedule()` a workflow from it, never await; workflow bodies use `MyType.ref()`, `spawn()`, `state`-named inline writers.
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
servicer before the first test):

<!-- generated:start reading-list front-door=mcp-ui step=auth -->
- `python/references/auth-allow-deny.md` — `allow()` only for genuinely public endpoints, never to silence dev warnings, pass tests, or mark "internal-only" methods; `deny()` locks a method out; return an instance.
- `python/references/auth-allow-if.md` — `allow_if(all=[...])` or `allow_if(any=[...])`, never both, never nested; `all` short-circuits in order; `is_app_internal` in `any` turns anonymous callers' `Unauthenticated` into `PermissionDenied`.
- `python/references/auth-built-in-predicates.md` — `has_verified_token`, `is_app_internal` and `state_id_is_user_id` and their common compositions; a self-scheduled workflow needs `is_app_internal`; predicates always take `**kwargs`.
- `references/auth-oauth-providers.md` — The launch provider fixes the user-ID namespace, so switching later strands user state; `OAuthProviderByEnvironment(dev=Development(), prod=Google(...))`, credentials as secrets, the `/__/oauth/callback` URL.
- `python/references/servicer-authorizer.md` — Write real rules on every servicer before the first test; list the tokenless call paths first; identity does not cross servicer calls; `oauth=` vs. the `token_verifier=` escape hatch.
- `python/references/auth-custom-predicates.md` — Per-method rules via `<Type>.Authorizer(method=rule, _default=rule)`; keyword-only predicates ending in `**kwargs`, annotated or `mypy` fails; check `context.app_internal` first; `PermissionDenied` vs. `Unauthenticated`.
- `python/references/auth-external-api-calls.md` — only when calling an external service's API as the user.
- `references/auth-store-tokens.md` — only when the app acts as the user at its own identity provider's API.
- `python/references/stdlib-oauth-tokens.md` — only when storing a user's OAuth tokens for an external service.
- `python/references/auth-claims.md` — only when you use claims or `set_claims`.
- `references/auth-custom-oauth-provider.md` — only when none of the shipped OAuth providers fits.
<!-- generated:end -->

**Before the frontend:**

<!-- generated:start reading-list front-door=mcp-ui step=frontend -->
- `references/react-scaffolding.md` — Copy `build/templates/mcp-ui/frontend/`; `vite.config.ts` exactly: flattening output breaks UI discovery at `frontend/dist/mcp/<name>/index.html`. `npm install` before the second `rbt generate`.
- `references/react-app-tsx.md` — No-id `use<Type>()` returns `{ <type>, isLoading }` resolved from the tool-call target — render a child once the handle exists; import `@api/<pkg>/v1/<name>_rbt_react`; composing reader for many actors.
- `python/references/react-generated-client.md` — What `rbt generate --react=` emits: `use<Type>()` overloads, three-field reader returns, mutations resolving to `{ response, aborted }` instead of throwing, typed errors, snake-to-camel naming.
- `references/pop-out-to-web-app.md` — only when a widget needs a "pop out into the web app" button.
<!-- generated:end -->

**Before the tests:**

<!-- generated:start reading-list front-door=mcp-ui step=tests -->
- `python/references/patterns-idempotency.md` — What `IdempotencyUncertainError` means and when a retry needs an idempotency key; replayed calls return the first run's response; idempotent `create` / `initialize`; UUIDv7 for insertable records.
- `python/references/testing-features.md` — The built-in steps' exact spelling (who calls, `creates` / `does`, saved values, `eventually`, aborts, tasks), `@wip` / `@blocked`, feature / rule / scenario shape, custom steps, mocks.
- `python/references/testing-project-setup.md` — `tests/` layout; the template's `pytest.ini` (three paths, or generated `_rbt` imports fail) and fixture (`allowed_origins=[]`); `reboot[dev]`, no `pytest-asyncio`; never construct servicers directly.
- `python/references/testing-external-context.md` — only when writing custom steps or harness tests.
- `python/references/testing-failure-recovery.md` — only when the app has a spawned task, a `Workflow`, or scheduled work.
- `python/references/testing-harness.md` — only when writing custom steps.
<!-- generated:end -->

The order of work around the feature files (agree in English, tag
`@wip`, iterate on scenarios) is the [`feature` skill](../feature/SKILL.md).

**Before running the app:** the [`run` skill](../run/SKILL.md).

If you find yourself grepping the framework's installed source or a
generated file to answer a question, stop: build's "Never Read
Generated or Installed Source in the Main Thread" is for you.
