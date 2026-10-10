---
name: build
description: The shared design-and-build flow every Reboot app with a frontend follows, reached from the app, mcp-ui and web-app skills (use it through one of them, with that front-door skill open) — design phase, state model assessment, the build steps in dependency order (API definition → project shell → servicer → authorizers → frontend → tests → run) and the update flow for an existing app.
argument-hint: [<app-description>]
allowed-tools: Bash, Read, Write, Glob, Grep, Edit
---

# build — Design and Build a Reboot App

> **Version notices:** if `rbt` reports a version mismatch or a newer
> Reboot, follow the [upgrade skill](../upgrade/SKILL.md).

The build flow for every Reboot app with a frontend, reached from a
**front-door skill**: [`mcp-ui`](../mcp-ui/SKILL.md) (an MCP host such
as ChatGPT or Claude), [`web-app`](../web-app/SKILL.md) (a standalone
browser SPA), or both. Keep the front-door skill open: it holds that
front door's concepts, the project layout, and each step's reading list
under **"Which References to Read, and When"**. Differences are marked
inline (`mcp-ui: … / web-app: …`); a dual-frontend app does both.
Backend-only work starts from the [`python` skill](../python/SKILL.md).

The flow is the **Reboot Flywheel**'s first two stages
([`references/flywheel.md`](references/flywheel.md)): **Design** runs
through Step 1 and ends when the user accepts the domain model and the
feature files ("Accept the Design"); **Prove** is Steps 2–7, building
to that accepted design. A change that alters the design goes back
through the acceptance.

<!-- generated:start catalog skill=build -->
**Lookups**
- `references/evidence.md` — Evidence for Merge and Promote
- `references/flywheel.md` — The Reboot Flywheel
<!-- generated:end -->

## Reading References

Everything read is re-sent every later turn:

- Read each reference **once**, at the step that needs it.
- **One reference per tool call**; `cat`-ing several can exceed the
  output limit and be cut off unseen.
- Skip a reading-list line ending *only when …* unless it holds.
- When a reference is wrong or silent about something you hit, append
  an item to the project's `FINDINGS.md` (format inside it) and keep
  going; the `report` skill files them later.

### Never Read Generated or Installed Source in the Main Thread

`*_rbt.py`, `*_rbt_react.ts`, `site-packages/`, `node_modules/` and
codegen templates run to tens of thousands of lines. Use the references
instead:

- React client: `python/references/react-generated-client.md` (web-app
  also `web-app/references/react-client.md`). Never open
  `frontend/api/**` or `web/src/api/**/*_rbt_react.ts` to check a call.
- Servicer signatures: `python/references/api-methods.md`; other backend
  shapes: the rest of `python/references/`.
- A scenario failing for a seemingly framework reason:
  `python/references/patterns-idempotency.md` and
  `patterns-common-gotchas.md` before `site-packages`.

Uncovered? Bound the output: `grep -n … | head -40` or
`sed -n '<start>,<end>p'` over a known range — never a whole generated
file or an unbounded recursive grep.

## Settle the Design, Then Build

**Settle the design before code**: wrong entities, field types or
method types mean regenerating a dozen or more files.

### Design Phase

0. Per capability, follow the [`feature` skill](../feature/SKILL.md):
   agree on it in plain English and write a `@wip` feature file before
   the API exists. The design derives from those features. Its Step 2a
   (run each scenario and see it fail) needs Step 2's project shell and
   test module: do it right after Step 2, before Step 3.
1. **Implement the brief literally** — the interactions the user
   described, not a pattern "common on sites like this". List any
   deviation (extra confirm step, staging area, batching) with its
   reason and ask first (select-then-confirm where the brief said
   "click to hold" is rework).
2. Run the State Model Assessment below.
3. State the design:
   - Application types: state shape (fields, types, tags).
   - Method map, one line per method: its method type
     (Reader/Writer/Transaction/Workflow) and its AI role (a tool the
     AI calls, a `UI()` view, or human-only), even when the MCP UI
     comes later.
   - Auth per method: anonymous, signed-in, owner only, app-internal,
     or by role. Where the domain has roles (front desk and
     housekeeping, editors and readers), name them and the methods each
     may call; roles live in state, checked by a custom predicate
     (`python/references/auth-custom-predicates.md`).
   - History: for each rule someone will later have to explain (an
     approval, a refund, anything that waits on a person or a provider),
     the events the owning state records: who, when, which step, the
     provider's reference. The runtime keeps no history the design
     doesn't name; the `inspect` skill reads only what is stored.
   - Demo data: a believable dev dataset (a dozen rooms on three floors,
     not one), seeded only under `rbt dev`, so every view has something
     to show the first time it opens
     (`python/references/lifecycle-seeding.md`, "Demo data").
   - Ready for both front doors, whichever is built first: a `User`
     type, and a `description=` on every method written for the AI. A
     method's description can't be edited once deployed (Reboot
     intends an upstream fix); switching `mcp=` later can (`python/references/api-schema-evolution.md`).
   - The look: a five-line visual brief (who and on what screen, the
     task, the one question the primary view answers, the accent and its
     real source (the user's or organization's brand) or "Reboot
     default, no brand supplied", the type choice) and the primary view chosen for
     the task: a list for triage and lookup, a board for a few items
     through stages, a chart or timeline over time
     (`web-app/references/ui-design.md`, principles 01–02). Light and
     dark both designed; web-app: a toggle between them in the first
     build, named in the design; mcp-ui: the host's theme, followed
     (`mcp-ui/references/ui-design.md`).
   - mcp-ui: the `User` type and its methods (the front door that
     creates and locates application-type instances); which methods get
     `UI()`; the AI's tool surface; ~3 example prompts, most ending on a
     turn that renders a `UI()`.
   - web-app: the SPA's pages and the methods each calls; the visual
     brief per `web-app/references/ui-design.md`.
Updates start with the design too (Update Flow).

### Writing the Design for a Human Reader

The reader hasn't read the skill files; make the design stand alone:

- **No skill-internal terms.** `Shape A` / `Shape B` / `Shape C` → the
  structure (`list[Sub]` of inline sub-records, `list[str]` of foreign
  state IDs, `OrderedMap` of foreign state IDs). "Non-state `Model`" →
  "a sub-record with no identity of its own". Drop citations like
  `Gotcha #N`, `state-collections.md`, `api-pydantic.md`, `gotchas.md`;
  explain the rule inline if it matters. `factory=True`,
  `Field(tag=N)` and raw pydantic spellings only when the spelling is
  the decision.
- **Every choice gets what + why**: the structure, method type or
  route, plus a one-clause domain reason ("grows without bound, so we
  paginate"; "logged-in users only, because the document is
  per-account"). A precise type name is fine when paired with that
  reason; the rule is no bare jargon.

> BAD: `people_index_id: str` — ID of an OrderedMap actor that holds
> this user's Persons (Shape C from state-collections.md — unbounded).
>
> GOOD: `people_index_id: str` — points to an OrderedMap that holds
> this user's Persons. An OrderedMap (rather than an inline list)
> because a PRM grows without bound and the UI will paginate / sort by
> recency.

## State Model Assessment

1. **Application types — decompose aggressively.** Every entity the
   user will add / edit / list / `find` over time (people, posts,
   tasks, documents, accounts) is its own `Type` with its own state,
   even if each user has only a few. Packing them into one parent
   (usually `User`) as `list[Person]` / `list[Post]` / `list[Task]`
   flattens N actors, blocks per-entity auth/methods, and
   forces a rewrite as it grows. A collection **synced or scraped from
   an external system** (a repo's issues, a mailbox) is an entity
   collection, unbounded by definition. Signals:
   `python/references/state-collections.md` Step 1. Counter-test: items
   one action must change all-or-none ("hold these 4 seats") stay
   inline on one actor, which is the lock (its "Counter-test:
   cohesion").
2. **`User`: always** — the MCP front door, and the owner of per-user
   state in the web app; route creation through it in both. `User`
   holds identity and the **IDs** of what it owns; unrelated concerns
   (auth/session, persona, background-engine config, caches) are their
   own Types, or its writers serialize
   (`python/references/state-actor-decomposition.md`).
3. **Container shape per collection** — the parent stores
   **references**, not objects (table and worked example in
   `state-collections.md`):
   - `list[Sub]` of non-state `Model`s — bounded sub-records with no
     identity (line items, tags). NOT for entity collections.
   - `list[str]` of foreign state IDs — a bounded entity collection
     (low hundreds, occasionally low thousands) always read whole.
   - `OrderedMap` of foreign state IDs — unbounded, or needs
     pagination, range queries or ordered iteration. The default for
     anything the user keeps adding to or that is externally synced.

   **Boundedness is a domain fact**: if you add a cap
   (`MAX_ITEMS = 40`) to make a collection bounded, it is unbounded —
   use `OrderedMap`.
4. **Creation.** Each application type is created by a `Transaction` on
   its owner (typically `User`) that calls `<Type>.create(context)` and
   registers the new ID in the owner's container; the type's own
   constructor is a `create` Writer with `factory=True`.
5. **State shape.** Every field has `Field(tag=N)`, a zero-value default
   and `description=`. A nested `Model` owned 1:1 by a parent state is
   `Optional[X] = Field(tag=N, default=None)`, hydrated in the parent's
   factory `create` Writer; non-Optional `Model`-typed fields reject
   `default=` / `default_factory=`. Rules: `python/references/api-pydantic.md`
   (mcp-ui also `mcp-ui/references/api-state-shapes.md`).
6. **Method type.** `Reader`: read-only. `Writer`: one state.
   `Transaction`: anything touching more than one state instance (a
   transfer; `User` creating an application-type instance). `Workflow`:
   long-running control flow (loops, scheduling, idempotency helpers)
   and every external-service call.
7. **Identity.** A singleton created in `initialize`, or many with
   their own IDs?
8. **Stdlib before your own types**: durable FIFO `Queue`;
   sorted/paginated map `OrderedMap`; who's-online `Presence`;
   broadcast `Topic` (PubSub); payload envelopes `Item`; a provider's
   OAuth tokens `OAuthTokenManager`; a secret/API key/PII field
   `Ciphertext`. Never declare a `Model` with one of those names — it
   forfeits durability, ordering and concurrency guarantees. Register
   each in `servicers/registry.py`, its `<thing>.servicers()` and
   `<thing>_library()`: a missing one fails on first call with an
   unknown-state-type error; a missing library dependency (e.g.
   `ordered_map_library()` for `Ciphertext`) fails at startup with
   `Missing required libraries: …`.
9. **Backend LLM calls** use the durable
   `reboot.agents.pydantic_ai.Agent`, never a raw `anthropic` / `openai`
   SDK or bare `pydantic_ai.Agent` (re-bills the provider on every
   workflow replay) (`python/references/agent-pydantic-ai.md`).
10. **Front-door surface.** mcp-ui: `mcp=Tool()` (AI-callable) vs.
    `mcp=None` per method; a `UI()` goes on the entity's own `Type` when
    the AI passes an entity ID, on `User` when it is about the user as a
    whole (mcp-ui skill, "UI Placement"). web-app: the pages and the
    methods each calls, through generated React hooks.

### When Correct Decomposition Fights the UI

One hook on one actor tempts you to flatten a collection into
`list[Item]`. **The data model wins**: keep one actor per item with an `OrderedMap` index on the
parent, and add a **composing reader** on the parent — a `Reader` that
ranges one page of IDs, reads each item actor, and returns hydrated
items plus a `next_cursor`. The page subscribes to that reader;
fan-out is server-side. mcp-ui: `mcp-ui/references/react-app-tsx.md`.
web-app (summary vs. detail readers, aggregation, per-caller views):
`python/references/patterns-cross-actor-reads.md`.

## Step-by-Step Build Flow

**Run all commands from the application directory**; before each step,
read its front-door reading list. Step 1 closes Design; "Accept the
Design" sits between it and Step 2, where Prove begins.

**Before step 1, start the developer dashboard** with the
[`dashboard` skill](../dashboard/SKILL.md) so the user watches the API
take shape (it stubs `pyproject.toml` / `.rbtrc` if absent). If it
fails, say so in a sentence and keep building.

### Step 1 — API definition

Read "Before the API definition". Name the project
once, in the design: kebab-case `<project>` (`todo-list`) and snake_case
`<app>` (`todo_list`), the API package and module; `<app>` also names
the `.mypy.ini` ignore stanza (`[mypy-<app>.v1.<app>_rbt]`), imports and
test module, so fix it before step 2. Write `api/<app>/v1/<app>.py`:
every `Field` with a tag, zero-value default and `description=`; every
method with `description=` and an explicit `mcp=` (required on all four
factories).
- mcp-ui: `mcp=Tool()` on what the AI calls, `mcp=None` otherwise;
  `UI()` methods per the design.
- web-app: `mcp=None` everywhere and no `UI()` until an MCP UI is
  added; descriptions are already written for the AI.

Then tell the user the state types you wrote, one line each in the
design's words: its name, what one holds, whose it is, and its methods
by name with what each lets someone do ("**Site**: one per connected
Analytics property, with its cached numbers. `overview` shows the
numbers for a period; `refresh` fetches new ones from Google"). Do it
again, marking what changed, whenever a later step adds, removes or
reshapes a state type or method.

### Accept the Design

Design ends here: the domain model (`api/`, generated) and the `@wip`
feature files exist, and no implementation does. The first time a
project reaches this point, open with the design card
([`references/flywheel.md`](references/flywheel.md), "Stage cards").
Show the **review table**, one row per rule, in the design's words:

| State type | State ID | Rule | Method | Kind | Who may call | Scenario |
| --- | --- | --- | --- | --- | --- | --- |
| `Room` | hotel and room number | booked at most once per night | `book` | Writer | the app itself (from `Reservation.create`) | "A second guest requests a booked room" |

Every rule in a feature file gets a row; a rule with no owner, method
or scenario is a gap to name, not to fill silently. List the feature
files by path, and point at the dashboard's Models and Features pages.
Then ask the user to accept, or to say what to change.

**Stop and wait.** No answer is not acceptance. A change sends you back
to the design (or the feature skill), then here again. Only when the
user said up front to build without stopping ("just build it", "don't
check with me"): show the table and continue, and the handoff says the
design was not accepted.

Once accepted, Step 2 records it in the repository (its item 5): the
review table in `design/review.md`, the record `scripts/model_diff.py
--accept` writes in `design/accepted.json`, and one commit holding
them with `api/` and the feature files. Every later model diff measures
from that commit.

### Step 2 — Project shell

Read "Before the project shell". Copy `templates/<front-door>/` with
its `copy.sh --merge` (see [`templates/README.md`](templates/README.md));
never retype a scaffold file from memory or a reference. `--merge`
fills `__project__` / `__app__` / `__Title__`, renames paths, keeps
every file the project already has (step 1's API file, a `CLAUDE.md`)
and lists them, and replaces the dashboard's stub `.rbtrc`,
`pyproject.toml` and `.python-version` with the template's (the
dashboard keeps running: both name the same directories). The sample
servicer, feature, test module and UI (a counter) are replaced in steps
3, 5 and 6; a dual-frontend app copies `templates/both/` (MCP UIs in
`frontend/mcp/`, the SPA in `frontend/web/`, one Vite server and one
generated client). Then:

1. `uv sync`.
2. `uv run rbt generate`. Don't read the output; the servicer signature
   is in `python/references/api-methods.md` ("The Servicer Signature
   Each Declaration Obliges").
3. Adapt `backend/src/main.py`
   (`python/references/lifecycle-application-entry.md`): servicer
   classes (not instances) and stdlib libraries go in
   `backend/src/servicers/registry.py`, which `main.py` and the test
   module both take; then `initialize`, `oauth=`
   (Step 4). mcp-ui: also `backend/src/example_prompts.py` →
   `Application(example_prompts=...)` (`mcp-ui/references/project-shell.md`).
4. `AGENTS.md` is the project's map for a coding agent, and `CLAUDE.md`
   is one line, `@AGENTS.md`. `--merge` keeps a `CLAUDE.md` the project
   already had: move its content into `AGENTS.md` and leave
   `@AGENTS.md` as its only line. Keep `AGENTS.md` current as you go:
   each new state type, UI, route or script adds its row.
5. **Record the acceptance** (skip when the user built without
   stopping): write `design/review.md` (the review table as shown, the
   feature files by path, the user's words if they gave any), run
   `python3 scripts/model_diff.py --accept`, and commit `api/`,
   `tests/*.feature` and `design/` with the scaffold as
   `Design accepted: <title>`, the project's first commit. That commit
   is the base every later `model_diff.py` measures from, and what the
   pull request and the release record mean by "accepted".

### Step 3 — Servicer

Read "Before the servicer". Write `backend/src/servicers/<app>.py`: an
`async def` per method, context type matching the factory. Writers
mutate one actor; cross-actor and external calls go in a `Transaction`
or `Workflow`. Add each new servicer class to `servicers/registry.py`,
the one list `main.py` and every test module take. Seed in `initialize` per
`python/references/lifecycle-seeding.md` (aliased, batched, sequential).
mcp-ui: `UserServicer` and `<X>.create(context)` in
`mcp-ui/references/servicer-patterns.md`.

### Step 4 — Authorizers

Read "Before the authorizers". **Write a real `authorizer()` on every
servicer now, before any test**: `rbt dev` only logs
`*** <Type>.<Method> IS MISSING AUTHORIZATION ***`, but the `Reboot()`
test harness, `rbt serve` and Reboot Cloud deny with `PermissionDenied`
(modes: `python/references/servicer-authorizer.md`).
`python3 scripts/model_diff.py HEAD` names any servicer still without one.

- **Identity**, same for both front doors:
  `Application(oauth=OAuth(provider=OAuthProviderByEnvironment(dev=Development(), prod=...)))`
  (`OAuth` from `reboot.aio.auth.oauth`, providers from
  `reboot.aio.auth.oauth_providers`). `Development()` is a real
  provider under `rbt dev`: a fake account picker with five identities
  (Alice, Ben, Carlos, Dani, Esi) issuing a verified, stable `dev-{hash}`
  `context.auth.user_id`; every other environment gets `prod`. Both arms
  are required and a selected `None` arm fails startup, so `prod=None`
  is fine until you pick a provider. Servicer code doesn't change
  between providers.
- **Rules** are production-shaped from day one:
  `allow_if(all=[state_id_is_user_id])` for one user's state;
  `has_verified_token` or custom predicates for shared state. A `User`
  servicer needs no `authorizer()` (its enforced default is
  production-worthy). Calls from `initialize`, `schedule()` and other
  servicers are app-internal with **no user identity**; list them first
  and add `is_app_internal`.
- **`allow()` only for genuinely public endpoints** (health checks,
  public sign-up or catalog reads); it survives into production, so
  never use it to quiet the dev warning or a failing test.
- **Pick the production provider before real users**, because user IDs
  are namespaced per provider and switching strands all user-keyed
  state. `Development` is dev-only; don't launch on `Anonymous` to
  "upgrade later"; `Google` / `GitHub` give only a user id; `Auth0` when
  the app needs user management. Without `claims=[...]` the app gets
  only an opaque user id and `set_claims` is never called
  (`python/references/auth-claims.md`).
- **`allowed_origins`.** Outside `rbt dev run`, an app with `oauth=`
  won't start without explicit `OAuth(..., allowed_origins=[...])`:
  each cross-origin sign-in origin, or `[]` for same-origin only.
  `rbt dev run` auto-allows `http://localhost` and `http://127.0.0.1` on
  any port, hiding the gap until first deploy
  ([`deploy` skill](../deploy/SKILL.md)). mcp-ui with no browser SPA:
  `[]`. web-app: the SPA is cross-origin by construction (own port in
  dev, own host in prod); list its origin.
- **`token_verifier=`** is the escape hatch: an IdP no `oauth=`
  provider covers and you can't wrap as an `OAuthProvider` subclass (an
  enterprise SAML/OIDC broker), or custom token semantics. They compose:
  Reboot's verifier runs first; non-Reboot-minted tokens fall through
  to yours.

### Step 5 — Frontend

Read "Before the frontend".
1. The template brought the shell — mcp-ui: `frontend/`, one bundle per
   UI under `frontend/mcp/<name>/`; web-app: `web/`. Versions are pinned
   to what the plugin ships; don't regenerate with
   `npm create vite@latest` (emits React 19 / TypeScript 6).
2. `npm install` in `frontend/` or `web/`.
3. `uv run rbt generate` again — the React bindings need `node_modules`.
4. Write the UI from the references.
   mcp-ui: `UI()` bundles per `mcp-ui/references/react-app-tsx.md`;
   copy `vite.config.ts` exactly. web-app: provider, `VITE_REBOOT_URL`,
   sign-in and typed errors per `web-app/references/react-client.md`;
   accessible markup (paired labels, named buttons, captioned tables)
   from the start so scenarios can drive the page; the look per
   `web-app/references/ui-design.md`.
   Every page the browser opens has a favicon: the template's
   `index.html` ships a placeholder, the title's initial on the accent.
   Keep it, or swap in the brand's mark in its colors; never ship
   without one (the browser then asks for `/favicon.ico` and logs a
   404 on every page). An MCP UI needs none: the host frames it.
5. `npm run build` there (sanity check). web-app: start the app now
   with the [`run` skill](../run/SKILL.md) (Step 7 only hands it off),
   then `uv run --with playwright python scripts/screenshots.py <routes>` saves every
   route at desktop and phone width, light and dark; open and check each
   against `ui-design.md` principles 03–09 and its Never list, fix
   what fails in one pass, then pin it with a look scenario per page.
   Name any deviation from the plan's own specs in the handoff.
6. **Responsive to the person, by Google's "good" thresholds**
   (Core Web Vitals, and RAIL for input):
   - **Loads:** a page's content, the data and not its skeleton, on
     screen within 2.5 s (LCP's threshold), and the layout steady as it
     arrives (CLS ≤ 0.1: skeletons shaped like the content).
   - **Input:** every click and keypress answered within 100 ms, the
     next frame ideally (RAIL; INP's threshold is 200 ms): the button
     shows its pending state at once, the result follows. Never block
     a handler on work the person didn't ask to wait for.
     (`page_timing.py` doesn't measure input; hold to this by
     construction.)

   Time the loads on every route, cold and warm, against the local
   backend with the demo data. web-app: with the app running, on the
   production build, not Vite's dev server:

   ```sh
   (cd web && npx vite build --mode development --outDir dist-timing \
     && npx vite preview --outDir dist-timing --port 4273 --strictPort) &
   uv run --with playwright python scripts/page_timing.py <routes>
   ```

   (`--mode development` keeps the minified production bundle and reads
   `.env.development`, so it calls the local backend.) Dual-frontend:
   `npm run build` in `frontend/`, then the script alone; the backend
   serves the build. It prints each route's worst content time, LCP
   and CLS and exits 1 over a threshold. Locally the network is free,
   so a slow load is the bundle (a route's code split out with
   `lazy()`, no heavy library on the first screen) or, far more often,
   a reader the page waits on that does too much
   (`python/references/patterns-cross-actor-reads.md`: one fan-out
   deep, materialize on write). Fix what you can in one pass; name each
   route still over, with its numbers and cause, in the handoff; stop
   the preview (`pkill -f 'vite preview --outDir dist-timing'`). MCP UIs render inside the host, which no script times:
   hold them to the same thresholds by keeping each to one reader and a
   small bundle.

### Step 6 — Tests

Read "Before the tests". **Write and run every design feature's
scenarios before handoff**, in the built-in steps of
`python/references/testing-features.md`:
- mcp-ui: every action the user should _do_ through the tool surface
  ("add an item and see it listed"), calling the methods the tools call.
- web-app: every UI action ("submit the form and see the result");
  click-through flows are web app scenarios per
  `python/references/testing-web-app.md` (needs `playwright`,
  `pytest-playwright`, `uv run playwright install chromium`).

- Every step names its caller; `"alice" is an authenticated user`
  exercises real authorizers.
- Register the **real** servicers; never subclass one to weaken its
  `authorizer()`.
- With `oauth=`, the fixture passes it as the template does:
  `OAuth(provider=OAuthProviderByEnvironment(dev=development,
  prod=development), allowed_origins=[])`, because the harness is
  neither `rbt dev run` nor `rbt serve`
  (`python/references/testing-project-setup.md`); keep a production
  `token_verifier=`.
- Seed per test, only what each scenario needs
  (`python/references/lifecycle-seeding.md`); let factories make ids up.
- When a value depends on **who is calling**, assert it across every
  actor hop: shared state crosses an actor boundary, the caller does not.
- Tag what can't pass yet `@blocked` with its reason; leave `@wip` where
  work continues.

Run `uv run pytest`, then `uv run mypy backend/ tests/` from the project
root (config: `python/references/lifecycle-project-setup.md`); proceed
only when every scenario passes (or is `@blocked`) and mypy is green.
Each scenario boots the app, so the suite takes minutes: run it in the
foreground with a timeout that covers the whole run and wait for the
result. Never leave it in the background and end your turn: nothing
brings you back to report it. A run silent for several minutes is
stuck on a scenario; rerun with `-x -v` to name it. Point the user at the dashboard's Features page (web-app:
and the browser recordings).

### Step 7 — Run

Follow the [`run` skill](../run/SKILL.md), the one start procedure;
never bare `rbt dev run` / `npm run dev`.
- mcp-ui: hand off the **setup wizard** at the backend root, not the
  `/mcp` URL; MCPJam launches on demand from it (mcp-ui skill, "Setup
  Wizard and MCPJam").
- web-app: check the page at the URL a person would type
  (`localhost`).

**Hand off** only after the final test run has finished. Open with the
prototype card ([`references/flywheel.md`](references/flywheel.md),
"Stage cards"), then:

1. The app's URL (mcp-ui: the setup wizard's; web-app: the page's).
2. The result: scenarios passed, anything `@blocked` and why, mypy
   clean, each route's load against the thresholds (Step 5) with any
   still over and its cause.
3. Every deviation from the brief or from the plan's own specs, with
   its reason (Design Phase, Step 5).
4. The state types and methods as built, one line each (Step 1), when
   they changed after the design; and whether the design was accepted
   ("Accept the Design"), as `python3 scripts/model_diff.py` says. A
   pull request's body follows
   [`references/evidence.md`](references/evidence.md).
5. `AGENTS.md` current (Step 2.4), and the `FINDINGS.md` items added;
   when there are any, offer the [`report` skill](../report/SKILL.md).
6. Unless the user asked for only one front door, the one-line offer of
   the other (`app` skill, "At handoff").

## Update Flow

1. Read `.rbtrc`, the API definition, servicer, `main.py` and the
   frontend entry (mcp-ui: `frontend/mcp/<ui-name>/App.tsx`; web-app:
   `web/src/App.tsx`).
2. Assess state model changes; with persisted state or a deploy, follow
   `python/references/api-schema-evolution.md`.
3. Agree on the feature in English and write its `@wip` feature file
   before the API changes ([`feature` skill](../feature/SKILL.md)).
4. Update the API (every new property with `description=`) →
   `uv run rbt generate`. Tell the user any state type or method added
   or changed, one line each (Step 1). Run
   `python3 scripts/model_diff.py` (it measures from the accepted
   design; `HEAD` as the base when the project has no record): any
   design change goes through "Accept the Design" before step 5, and
   once accepted, `python3 scripts/model_diff.py --accept` and a commit
   of `api/`, `tests/*.feature` and `design/` ("Design accepted:
   <what>") record it. None (a new scenario under an existing rule, a
   code fix) stays in Prove.
5. Update servicer methods, and the authorizer of any servicer whose
   methods changed, as the accepted "Who may call" says. An authorizer
   change the accepted design didn't name is a design change: back to
   step 4's gate.
6. Update the frontend. mcp-ui: a new user-facing capability gets an
   example prompt in `backend/src/example_prompts.py`.
   web-app: components and routes, markup kept accessible; time each
   changed or new route against the thresholds (Step 5).
7. Update the scenarios (web-app: plus a web app scenario per
   click-through flow). Run `uv run mypy backend/ tests/` and
   `uv run pytest`; fix everything; ask before removing `@wip`.
8. If a file, command or rule changed, update `AGENTS.md` to match.
9. Not running: start it with the [`run` skill](../run/SKILL.md).
10. Close with the feature or fix card
    ([`references/flywheel.md`](references/flywheel.md), "Stage cards"):
    in full the first time, one line after.

**Adding the other front door** is an update like any other: load its
skill and make the project look like `templates/both/`.
- To a web app: copy `both/frontend/` and
  `backend/src/example_prompts.py`, move `web/src/` and
  `web/index.html` into `frontend/web/`, import the client from
  `@api/…`, and point `.rbtrc`'s `generate --react=` at
  `frontend/api` (one output directory per project; two `node_modules`
  would load React twice). Delete `web/`.
- To an MCP UI: copy `both/frontend/web/`, and fill `__Title__` and
  `__Initial__` in its `index.html`.
Then switch the AI's methods to `mcp=Tool()`, add any `UI()` methods,
write the new front door's scenarios, and take `AGENTS.md`'s
frontend rows from `templates/both/AGENTS.md`.
