---
name: build
description: The shared design-and-build flow every Reboot app follows — design phase, state model assessment, the build steps in dependency order (API definition → project shell → servicer → authorizers → frontend → tests → run) and the update flow. Reached from the app, mcp-ui and web-app skills; follow it together with your front-door skill, which holds what differs and the per-step reading lists.
argument-hint: [<app-description>]
allowed-tools: Bash, Read, Write, Glob, Grep, Edit
---

# build — Design and Build a Reboot App

> **Version notices:** if `rbt` reports a version mismatch or that a
> newer Reboot is available, the [upgrade skill](../upgrade/SKILL.md)
> says how and when to react.

This is the one build flow for every Reboot app with a frontend. You
arrive here from a **front-door skill** — [`mcp-ui`](../mcp-ui/SKILL.md)
(an MCP host such as ChatGPT or Claude) or [`web-app`](../web-app/SKILL.md)
(a standalone browser SPA) — or from both for a dual-frontend app.
Keep the front-door skill open beside this one: it holds the concepts
specific to that front door, the project layout, and, under
**"Which References to Read, and When"**, the reading list for each
step below. Where a step differs by front door this file says so
inline (`mcp-ui: … / web-app: …`); a dual-frontend app does both
branches. Backend-only work (no frontend) starts from the
[`python` skill](../python/SKILL.md) instead.

## Reading References

Everything you read stays in the conversation and is re-sent on
every later turn, so **read each reference at the step that needs
it**, not all up front, and read each one **once**. Read **one
reference per tool call**: `cat`-ing several at once can exceed the
tool's output limit and be cut off without reaching you. A reading
list line ending *only when …* is skipped unless that is true of
your app.

### Never Read Generated or Installed Source in the Main Thread

`*_rbt.py`, `*_rbt_react.ts`, `site-packages/`, `node_modules/`, and
codegen templates run to tens of thousands of lines. Every one you
open is re-sent on every remaining turn, which makes reading them
the most expensive way in the system to learn a fact.

The generated surfaces you need are written out in the references:
the React client contract in `python/references/react-generated-client.md`
(web-app also `web-app/references/react-client.md`), the servicer
signature each declaration obliges in `python/references/api-methods.md`,
the backend shapes in the rest of `python/references/`. Use them. In
particular, never open `frontend/api/**` or `web/src/api/**/*_rbt_react.ts`
to check a call. When a scenario fails for what looks like a reason
inside the framework, check `python/references/patterns-idempotency.md`
and `patterns-common-gotchas.md` before anything in `site-packages`.

If something genuinely isn't covered, bound the output hard: a
targeted `grep -n … | head -40`, or `sed -n '<start>,<end>p'` over a
known range. Never a whole generated file, never an unbounded
recursive grep.

## Settle the Design, Then Build

**Always settle the design before writing code.** The state model is
the foundation — getting entities, field types, or method types wrong
means regenerating a dozen or more files across the project.

### Design Phase

0. For each capability the app has, follow the
   [`feature` skill](../feature/SKILL.md): agree on it in plain
   English with the user and write it down as a `@wip` feature file
   before the API exists. The design is derived from those features.
1. **Implement the brief literally.** Build the interactions the user
   described, the way they described them — not a pattern that is
   "common on sites like this". If you think a deviation is needed
   (an extra confirm step, a staging area, batching), list each one
   with its reason and ask before building it. An invented
   select-then-confirm flow where the brief said "click to hold" is
   rework, and a panel explaining the invention makes it worse.
2. Analyze the description with the State Model Assessment below.
3. State the design you are about to build:
   - Application types: state shape (fields, types, tags).
   - Method map: which operations, which method type
     (Reader/Writer/Transaction/Workflow).
   - Auth: who may call each method — anonymous, signed-in, the
     owning user only, app-internal only.
   - mcp-ui: the `User` type and its methods (the front door that
     creates and locates application-type instances); which methods
     get `UI()`; the tool surface the AI will see; ~3 example prompts,
     most ending on a turn that renders a `UI()` (see the mcp-ui skill).
   - web-app: the route surface — which pages the SPA has and which
     methods each calls; whether there is per-user state (then a
     `User` type owns it).
4. Then follow the Step-by-Step Build Flow.

For updates to existing apps, still work the design first: read the
current state, state the changes, then modify (Update Flow below).

### Writing the Design for a Human Reader

The design is read by a **human who has not read the skill files**.
They are judging the design — entities, collections, methods, routes,
auth — not verifying that you followed the skill. Write so it stands
on its own.

**Don't quote skill-internal terms** when presenting the design.
They mean nothing outside the skills:

- `Shape A` / `Shape B` / `Shape C` — name the actual data structure:
  `list[Sub]` of inline sub-records, `list[str]` of foreign state
  IDs, `OrderedMap` of foreign state IDs.
- "non-state `Model`" — say "a flat sub-record that lives and dies
  with the parent" or "no identity of its own", in domain terms.
- `Gotcha #N` and filenames like `state-collections.md` /
  `api-pydantic.md` / `gotchas.md` — drop the citation; if the rule
  matters to the design, explain it inline.
- `factory=True`, `Field(tag=N)`, raw pydantic spellings — fine to
  mention briefly when the spelling itself is the design decision,
  but never as the explanation.

**For every design choice, give the what + the why.** The _what_ is
the concrete data structure, method type, or route. The _why_ is a
one-clause reason rooted in the user's domain ("grows without bound,
so we need pagination"; "no methods or auth of its own, so it lives
inline"; "logged-in users only, because the document is per-account").

Collection shape — BAD, uses skill-internal terms:

> `people_index_id: str` — ID of an OrderedMap actor that holds this
> user's Persons (Shape C from state-collections.md — unbounded).

Collection shape — GOOD:

> `people_index_id: str` — points to an OrderedMap that holds this
> user's Persons. An OrderedMap (rather than an inline list) because a
> PRM grows without bound and the UI will paginate / sort by recency.

Nested model — BAD: "Relationship and Event are non-state Models —
Shape A." GOOD:

> Relationship and Event live inline on Person as
> `list[Relationship]` / `list[Event]`. They don't get their own state
> actors because they have no lifecycle, methods, or auth independent
> of the Person they belong to.

**Escape hatch.** When the precise type name _is_ what the reader
needs to see ("I'm proposing `OrderedMap` here, not `list[str]`"),
name the type — but pair it with the plain-English reason in the same
sentence. The rule is "no bare jargon", not "no technical terms".

## State Model Assessment

Before writing code, analyze the user's request:

1. **Application types — decompose aggressively.** List every
   distinct entity the user is going to add / edit / list / find over
   time (people, posts, tasks, documents, accounts, …). **Each entity
   becomes its own `Type` with its own state**, even when "each user
   only has a few of them". Anything you can imagine being `add`-ed /
   `remove`-d / `find`-ed by name has its own identity and belongs in
   its own actor. The default wrong move is packing everything into
   one parent's state (usually `User`) as `list[Person]` (or
   `list[Post]`, `list[Task]`, …) — that flattens N actors into one,
   prevents per-entity auth/methods, and forces a full rewrite when
   the collection grows. A collection the app **syncs or scrapes from
   an external system** (a repo's issues, a mailbox, an RSS feed) is
   an entity collection too, and unbounded by definition, even though
   the user never "adds" to it. Full signal list:
   `python/references/state-collections.md` Step 1.
2. **`User`?**
   - mcp-ui: always — `User` is the MCP front door.
   - web-app: only when there is per-user state; then route creation
     through `User` exactly as an MCP UI does (the pattern is
     independent of MCP). Anonymous apps, or apps where all users
     share state, skip it.

   Either way `User` holds identity and the **IDs** of what it owns;
   unrelated concerns (auth/session, persona, background-engine
   config, caches) are their own Types, or its writers serialize
   (`python/references/state-actor-decomposition.md`).
3. **Container shape for each collection.** Once an entity is its own
   `Type`, the parent stores **references**, not objects. Three shapes
   (full table and a worked example in `state-collections.md`):
   - `list[Sub]` of non-state `Model`s — bounded sub-records with no
     identity of their own (line items on an Order, tags on a Post).
     NOT for entity collections.
   - `list[str]` of foreign state IDs — a bounded entity collection
     (low hundreds, occasionally low thousands) you always read whole.
   - `OrderedMap` of foreign state IDs — grows without bound, needs
     pagination, range queries or ordered iteration. The default for
     any "list of things the user keeps adding to" and for anything
     synced from an external source.

   **Boundedness is a domain fact, not a number you pick.** If you
   catch yourself adding a size cap (`MAX_ITEMS = 40`) so a collection
   counts as bounded, it is unbounded — use `OrderedMap`.
4. **Creation methods.** Each application type is created by a
   `Transaction` on its owner (typically `User`) that calls
   `<Type>.create(context)` and registers the new ID in the owner's
   container. The type's own constructor is a `create` Writer with
   `factory=True`.
5. **State shape (per type).** Fields — lists, nested objects,
   primitives — each with `Field(tag=N)`, a zero-value default and a
   `description=`. A nested `Model` owned 1:1 by a parent state must
   be `Optional[X] = Field(tag=N, default=None)` and hydrated in the
   parent's factory `create` Writer; non-Optional `Model`-typed fields
   reject `default=` / `default_factory=`. Full rules in
   `python/references/api-pydantic.md` (mcp-ui also
   `mcp-ui/references/api-state-shapes.md`).
6. **Operations → method type.**
   - `Reader` — read-only queries.
   - `Writer` — single-state mutations.
   - `Transaction` — multi-state atomic operations (a transfer between
     two accounts; `User` creating an application-type instance). If
     any operation touches more than one state instance, it is a
     `Transaction`.
   - `Workflow` — long-running control flows with loops, scheduling,
     and idempotency helpers; every call to an external service.
7. **Identity per type.** A single well-known instance (a singleton
   created in `initialize`) or many, each with its own ID?
8. **Stdlib before your own types.** A durable FIFO is `Queue`, a
   sorted/paginated map `OrderedMap`, who's-online `Presence`,
   broadcast `Topic` (PubSub), payload envelopes `Item`, a provider's
   OAuth tokens `OAuthTokenManager`, a secret/API key/PII field
   `Ciphertext`. Import the stdlib actor — never declare a `Model`
   with one of those names, which forfeits durability, ordering and
   concurrency guarantees. Each stdlib reference gives its
   `<thing>_library()` registration. Forgetting it fails only when the
   type is first called, with an unknown-state-type error; a library
   whose own dependency (e.g. `ordered_map_library()` for `Ciphertext`)
   is missing fails at startup with `Missing required libraries: …`.
9. **Backend LLM calls** go through the durable
   `reboot.agents.pydantic_ai.Agent`, never a raw `anthropic` /
   `openai` SDK or a bare `pydantic_ai.Agent`, which re-bills the
   provider on every workflow replay
   (`python/references/agent-pydantic-ai.md`).
10. **Front-door surface.**
    - mcp-ui: which methods get `mcp=Tool()` (the AI may call them)
      vs. `mcp=None`; where each `UI()` goes — on the entity's own
      `Type` when the AI passes an entity ID, on `User` when the UI is
      about the user as a whole (mcp-ui skill, "UI Placement").
    - web-app: which pages exist and which methods each calls; the
      generated React hooks wrap the calls.

### When Correct Decomposition Fights the UI

The easy frontend path is one reactive hook on one actor, and it
quietly pressures you to flatten an entity collection into
`list[Item]` on a single actor so a page can read it in one
subscription. **The data model wins.** Keep the collection decomposed
— one actor per item, an `OrderedMap` index on the parent — and add a
**composing reader** on the parent: a `Reader` that ranges one page of
IDs, reads each item actor, and returns fully-hydrated items plus a
`next_cursor`. The page subscribes to that one reader; the fan-out
happens server-side. A demo-correct `list[Item]` that must be torn
apart once real data arrives is the failure this flow exists to
prevent.
- mcp-ui: the backend reader + React subscription are in
  `mcp-ui/references/react-app-tsx.md`.
- web-app: summary vs. detail readers, server-side aggregation and
  per-caller views are in `python/references/patterns-cross-actor-reads.md`.

## Step-by-Step Build Flow

**All commands run from the application directory.** At each step,
**read the references your front-door skill lists under that step**
before writing the step's files.

**Before step 1 — start the developer dashboard.** Load the
[`dashboard` skill](../dashboard/SKILL.md) and follow it, so the user
can watch the API take shape while you write it (it puts stub
`pyproject.toml` / `.rbtrc` files in place if none exist). If it fails
to come up, say so in one sentence and keep building; do not stop to
debug it.

### Step 1 — API definition

Read the "Before any code" and "Before the API definition" lists.
Name the project once, in the design: a kebab-case `<project>`
(`todo-list`) and a snake_case `<app>` (`todo_list`) that is the API
package and module. Write `api/<app>/v1/<app>.py` from the design:
every `Field` with a tag, zero-value default and `description=`;
every method with a
`description=` and an explicit `mcp=` (the keyword is required on all
four factories).
- mcp-ui: `mcp=Tool()` on what the AI calls, `mcp=None` otherwise;
  `UI()` methods per the design.
- web-app: `mcp=None` on every method; no `UI()`.

`<app>` is what the shell's `.mypy.ini` ignore stanza
(`[mypy-<app>.v1.<app>_rbt]`), imports and test module are named
after, so pick it before step 2.

### Step 2 — Project shell

Read the "Before the project shell" list. Copy `templates/<front-door>/`
(see [`templates/README.md`](templates/README.md)) — a complete
minimal project — never retype a scaffold file from memory or a
reference. Its `copy.sh` fills the `__project__` / `__app__` /
`__Title__` placeholders and renames paths, but refuses a directory
that already has an `.rbtrc` and would overwrite your API file with
the sample. So copy into an empty scratch directory, delete the
dashboard's stub `.rbtrc` and `pyproject.toml`, and merge without
clobbering (`cp -Rn <scratch>/. .`) so step 1's API file stays. The
template's sample servicer, feature, test module and UI (a counter)
are replaced in steps 3, 5 and 6. A dual-frontend app needs pieces of
both templates. Then:

1. `uv sync`.
2. `uv run rbt generate`. Don't read what it wrote: the signature your
   servicer must match is in `python/references/api-methods.md` ("The
   Servicer Signature Each Declaration Obliges").
3. Adapt `backend/src/main.py`
   (`python/references/lifecycle-application-entry.md`): servicer
   classes (not instances), stdlib libraries, `initialize`, and
   `oauth=` (Step 4).
   - mcp-ui: also `backend/src/example_prompts.py`, passed as
     `Application(example_prompts=...)` (`mcp-ui/references/project-shell.md`).

### Step 3 — Servicer

Read the "Before the servicer" list. Write
`backend/src/servicers/<app>.py`: one `async def` per method, the
context type matching the factory. Writers mutate one actor only;
cross-actor and external calls go in a `Transaction` or `Workflow`.
Seeding goes in `initialize` per `python/references/lifecycle-seeding.md`
(aliased, batched, sequential).
- mcp-ui: the `UserServicer` front door and `<X>.create(context)`
  pattern are in `mcp-ui/references/servicer-patterns.md`.

### Step 4 — Authorizers

Read the "Before the authorizers" list. **Write a real `authorizer()`
on every servicer now, before any test.** Without one, `rbt dev`
allows the call and logs `*** <Type>.<Method> IS MISSING AUTHORIZATION ***`
at most once a minute, but the `Reboot()` test harness — and so every
scenario in Step 6 — denies it with `PermissionDenied`, as
`rbt serve` and Reboot Cloud do. Deferring rules "until prod" only
moves the failure to the first test.

- **Identity** comes from `Application(oauth=OAuth(provider=OAuthProviderByEnvironment(dev=Development(), prod=...)))`
  (`OAuth` from `reboot.aio.auth.oauth`; the providers from
  `reboot.aio.auth.oauth_providers`), the same for both front doors.
  `Development()` is a real provider under `rbt dev`: a fake account
  picker with five identities (Alice, Ben, Carlos, Dani, Esi) issuing
  a verified, stable `dev-{hash}` `context.auth.user_id`. Every other
  environment gets `prod`. Both arms are required; a selected `None`
  arm makes the app fail to start, so `prod=None` is fine until you
  pick a real provider. Servicer code doesn't change between providers.
- **Rules.** Identity is wired the same in dev and prod, so
  production-shaped rules work immediately:
  `allow_if(all=[state_id_is_user_id])` for state that belongs to one
  user; `has_verified_token` or custom predicates for shared state. A
  `User` servicer needs no `authorizer()`: its default
  (`state_id_is_user_id` or `is_app_internal`) is enforced even in dev
  and is production-worthy. List the tokenless call paths first —
  `initialize`, `schedule()`, calls from other servicers are
  app-internal and carry **no user identity** — and add
  `is_app_internal` for them (`python/references/servicer-authorizer.md`).
- **`allow()` only for genuinely public endpoints** (health checks,
  public sign-up, public catalog reads). It means "public on the
  internet, no identity required" and survives into production; never
  use it to quiet the dev warning or a test failure.
- **Production provider — choose deliberately, before real users.**
  User IDs are namespaced per provider, so switching later strands
  every user-keyed piece of state. `Development` is dev-only; don't
  launch on `Anonymous` planning to "upgrade later"; `Google` /
  `GitHub` give a user id and nothing more; `Auth0` when the app needs
  user management. Without `claims=[...]` the app receives only an
  opaque user id and `set_claims` is never called
  (`python/references/auth-claims.md`).
- **`allowed_origins`.** Outside `rbt dev run`, an app with `oauth=`
  refuses to start unless `OAuth(..., allowed_origins=[...])` is set
  explicitly: list each browser origin that signs in cross-origin, or
  pass `[]` for same-origin-only. `rbt dev run` allows
  `http://localhost` and `http://127.0.0.1` on any port automatically,
  so the gap is invisible until the first deploy (the
  [`deploy` skill](../deploy/SKILL.md) covers production).
  - mcp-ui with no browser SPA: `allowed_origins=[]`.
  - web-app: the SPA is cross-origin from its backend by construction
    (its own port in dev, its own host in prod) — list its origin.
- **`token_verifier=`** is the escape hatch, not the default: for an
  IdP no `oauth=` provider covers and you can't wrap as an
  `OAuthProvider` subclass (an enterprise SAML/OIDC broker), or custom
  token semantics. The two compose: Reboot's verifier runs first, and
  any token that is not Reboot-minted falls through to yours.

### Step 5 — Frontend

Read the "Before the frontend" list.
1. The frontend shell came with the template — mcp-ui: `frontend/`,
   one bundle per UI under `frontend/mcp/<name>/`; web-app: the SPA in
   `web/`. Its versions are pinned to what the plugin ships; don't
   regenerate it with `npm create vite@latest`, which emits React 19 /
   TypeScript 6.
2. `npm install` in `frontend/` (mcp-ui) or `web/` (web-app).
3. `uv run rbt generate` again — the React bindings need
   `node_modules` to resolve types.
4. Write the UI from the references, not from the generated files.
   - mcp-ui: `UI()` bundles per `mcp-ui/references/react-app-tsx.md`;
     copy `vite.config.ts` exactly.
   - web-app: provider, `VITE_REBOOT_URL`, sign-in and typed errors
     per `web-app/references/react-client.md`; accessible markup
     (paired labels, named buttons, captioned tables) from the start,
     so scenarios can drive the page.
5. `npm run build` in the same directory (sanity-check the bundle).

### Step 6 — Tests

Read the "Before the tests" list. **Write and run the scenarios of
every feature before handing the app off.** Each feature file from
the design phase (the [`feature` skill](../feature/SKILL.md)) gets its
scenarios now, in the built-in steps of
`python/references/testing-features.md`:
- mcp-ui: every action the user should be able to _do_ through the
  tool surface ("create a new todo list", "add an item and see it
  listed"), calling the methods the tools call.
- web-app: every action in the UI ("submit the form and see the
  result"); the flows a person clicks through are web app scenarios
  per `python/references/testing-web-app.md` (they need `playwright`,
  `pytest-playwright` and `uv run playwright install chromium`).

Every step names who calls; a signed-in user is declared with
`"alice" is an authenticated user`, which is how the real authorizers
get exercised. Register the **real** servicers and never subclass one
to weaken its `authorizer()`. Leave `oauth=` out of the test's
`Application(...)` (the harness installs a test provider; keep a
production `token_verifier=` if the app has one). Seed per test, the
minimum each scenario needs (`python/references/lifecycle-seeding.md`).
Let factories make ids up. When a value depends on **who is calling**,
assert it through every actor hop it crosses — shared state survives
an actor boundary, the caller does not, and a green suite that never
crossed the hop misses it. Tag what cannot pass yet `@blocked` with
its reason; leave `@wip` where work continues.

Run `uv run pytest`, then `uv run mypy backend/ tests/` from the
project root (config in `python/references/lifecycle-project-setup.md`),
and fix every failure and error. Do not proceed until every scenario
passes (or is `@blocked` with a reason) and mypy is green — together
they catch contract bugs before the user does. Point the user at the
dashboard's Features page to review the features (web-app: and at the
recordings of the browser scenarios).

### Step 7 — Run

Load the [`run` skill](../run/SKILL.md) and follow it — the single
canonical "start the app" procedure. It makes sure dependencies and
secrets are in place and starts the backend and frontend. Don't
bypass it with bare `rbt dev run` / `npm run dev`.
- mcp-ui: the handoff is the **setup wizard** at the backend root, not
  the `/mcp` URL; MCPJam launches only on demand from the wizard
  (mcp-ui skill, "Setup Wizard and MCPJam").
- web-app: it hands the user the URLs and a first page to open; check
  the page at the URL a person would type (`localhost`), not only the
  one that happens to work.

## Update Flow

When modifying an existing app:

1. Read `.rbtrc`, the API definition, servicer, `main.py`, and the
   frontend entry (mcp-ui: `frontend/mcp/<ui-name>/App.tsx`; web-app:
   `web/src/App.tsx`).
2. Assess state model changes. If the app has persisted state or has
   been deployed, read `python/references/api-schema-evolution.md`
   for the rules API schema evolution must follow.
3. Agree on the changed or new feature in English and write it down
   first, per the [`feature` skill](../feature/SKILL.md): the feature
   file, tagged `@wip`, before the API changes.
4. Update the API definition (every new property with a
   `description=`) → `uv run rbt generate`.
5. Update servicer methods, and the authorizer of any servicer whose
   methods changed.
6. Update the frontend.
   - mcp-ui: when the change adds a user-facing capability, add or
     update an example prompt in `backend/src/example_prompts.py`.
   - web-app: components and routes, keeping the markup accessible.
7. Update the scenarios (web-app: and a web app scenario for a flow a
   person clicks through). Run `uv run mypy backend/ tests/` and
   `uv run pytest`; fix every error and failure before handing back,
   and ask before removing `@wip`.
8. If the app isn't running, bring it up with the
   [`run` skill](../run/SKILL.md). If it is running under
   `rbt dev run`, the `--watch` globs reload it automatically — no
   restart needed. Editing `.env` likewise triggers a restart, so a
   new or changed secret is re-read by `--env-file`.

Specific patterns and file shapes live in the references — read them
on demand based on what's changing.
