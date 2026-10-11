---
name: build
description: The shared design-and-build flow every Reboot app with a frontend follows, reached from the app, mcp-ui and web-app skills (use it through one of them, with that front-door skill open) — design phase, state model assessment, the build steps in dependency order (API definition → project shell → servicer → authorizers → frontend → tests → run) and the update flow for an existing app.
argument-hint: [<app-description>]
allowed-tools: Bash, Read, Write, Glob, Grep, Edit, AskUserQuestion
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
Every line to the user is a statement of fact about the app, in the
build's voice: the user reads the build as it happens, so each step
ends in two or three statements about their objects, rules and roles
and the decisions between them (what a stay holds, why a suite is its
own object, which rule a night enforces, who may cancel). Never an
account of what was done, never what comes next, never which reference
or step is in hand, never the first person: a sentence that starts
with I is rewritten before it is sent (`references/flywheel.md`, Tone).
Not "Reading the API references" or "The shell is in place; the API
comes next", but what they settled: "Each room is its own actor, so two
guests cannot hold the same night". A page or a question is said from the app's side, "the guest's
reservations", "the refunds waiting on a manager", never "my
reservations".

The sentences, so a newcomer understands on one reading: the first
sentence about an object says why it exists, the harm it prevents or
the job it does, with the object as its subject, and what it holds
comes after. Each sentence under about twenty words, one idea, an
active verb. The user's own nouns, and Reboot's own terms (actor,
writer, transaction, authorizer, scenario), each said in a few words
the first time. Facts stated directly, no hedging, no praise. No em or
en dashes, no semicolons, no parentheses, no headings or lists in the
narration, no closing sentence that sums up, and none of: crucial,
essential, vital, key, robust, seamless, leverage, delve, empower,
comprehensive, pivotal.

A new build whose first words to the user were not the `app` skill's
welcome says it now, word for word, before anything else.

**How the build talks**, the model to imitate, a hotel; write yours in
the user's nouns, this shape, this length, at every step:

> **Suites and stays.** The 23 suites are a fixed list on the hotel,
> one object each: a suite is the thing that is occupied, so it owns
> the rule that it hosts one stay per night, and its `hold` is a
> writer, called only by the app when a stay is booked. A stay is the
> guest's visit, its nights, its suite and its services, and is its own
> object because it grows through the visit and is what the butler
> reads: `book` is a transaction, because it holds every night or none;
> `request` is a writer the guest calls on their own stay; the butler's
> `requests` is a reader over every stay. The spa has capacity, so it
> owns the rule that a slot takes one guest; dinner seatings the same.
> Set aside: a calendar on each suite, which would grow without bound,
> and a single hotel object holding every stay, which would serialize
> every booking behind every other.
>
> The staff are one roster with roles, so the butler and the concierge
> see different things, and the first manager is named by a setting,
> never whoever signs in first. Assumed, open to change at the review:
> guests sign in with the development picker, local data is seed data,
> and a stay is paid at booking.

**The map, then the details.** Everything said serves one goal: the
user understands the app's structure. Three times, after the scope
round, once the API file is written and at the handoff, the build shows
the app at a glance, a table with one row per object, in the user's
nouns:

| Object, and the rules it owns | What it can do | Who may call it |
| --- | --- | --- |
| `Suite`, one of the 23: one stay per night | `hold`, a writer | only the app, when a stay is booked |
| `Stay`, a guest's visit: every night or none | `book`, a transaction; `request`, a writer | the guest; the butler reads |

Every other sentence names the row it changed and how. What leaves the
map unchanged goes unsaid: a typo fixed, a predicate's order, a lock
mode.

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
- **A step's whole list at once**: one Read per reference, all of them
  in a single turn as parallel calls. `cat`-ing several into one call
  can exceed the output limit and be cut off unseen.
- Skip a reading-list line ending *only when …* unless it holds.
- **A reference is narrated by what it settled.** After it, one or two
  statements of fact about the app ("the staff are one roster with
  roles, so the butler and the concierge see different things");
  nothing before it, nothing about the reference or the tooling it
  describes, nothing about what comes next. A silent read is a failure.
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

One round of scope questions comes first, then the first prototype:
design the whole app within that scope, build it complete, saying each
object and decision as it is made, and review it running. From there design is a conversation in slices: agree one
feature, show the slice of the model it adds, build it, hand it off.
"Just build it", said up front, skips the questions and the reviews'
waits.

0. **Scope first, in one round.** Before any design, ask what the
   brief leaves open with AskUserQuestion, at most four questions, each
   with two to four options, the simplest first and marked
   Recommended: which parts of the domain the first version covers
   (multi-select, in the user's nouns: reservations, housekeeping,
   rates); who uses it and in which roles; the one thing it must never
   get wrong. A question the brief
   already answers is skipped. Nothing is asked after this round. With
   no one to answer, take the recommended options and say so. The
   answers go into `design/design.md` under "Scope", the rest under
   "Assumed" (defaults: the web app, the `Development()` sign-in).
   Local data is seed data, reset when the model changes, never asked.
   Then one line: a simple, fast prototype of that
   scope goes up first, to review the architecture, the rules and the
   features on.
1. **The whole app, said object by object.** Write every capability's
   `@wip` feature file from the scope ([`feature`
   skill](../feature/SKILL.md), Step 2; its Step 2a is this flow's).
   As the model takes shape (items 3 and 4), say each object as it is
   created, in the user's nouns: what it is, why it is its own object,
   its methods with their kinds and callers, and the choice set aside
   ("`Night` rather than a calendar on `Room`: a room's calendar grows
   without bound"). Say each decision as it is made, with what it buys
   or costs; the decisions log keeps them (Step 2, item 5). After the
   review, each later feature follows the feature skill's Step 1:
   agree it in plain English, show its slice of the model as rows
   under the review table, build it, hand it off, ask what comes next.
2. **Implement the brief literally**: the interactions the user
   described, not a pattern common on sites like this. A deviation
   (an extra confirm step, a staging area, batching) is listed with
   its reason and asked first.
3. Run the State Model Assessment below.
4. State the design:
   - Application types: state shape (fields, types, tags).
   - Method map, one line per method: its kind (Reader, Writer,
     Transaction, Workflow) and its AI role (a tool, a `UI()` view, or
     human-only), even when the MCP UI comes later.
   - Auth per method: anonymous, signed-in, owner only, app-internal,
     or by role. Roles (front desk and housekeeping, editors and
     readers) are named with the methods each may call, live on one
     roster actor and are checked by a custom predicate
     (`python/references/auth-custom-predicates.md`); staff who sign
     in with roles follow `python/references/auth-roles.md`.
   - History: for each rule someone will later have to explain (an
     approval, a refund, anything that waits on a person or a
     provider), the events the owning state records: who, when, which
     step, the provider's reference. The runtime keeps no history the
     design doesn't name. Events go on the short-lived entity they
     explain, or in an `OrderedMap` or per-day actor, never on a
     singleton that lives as long as the app, since every write
     re-serializes the whole list
     (`python/references/state-collections.md`, Scales as).
   - Demo data: a believable dev dataset (a dozen rooms on three
     floors, not one), seeded only under `rbt dev`, so every view has
     something to show; a spatial domain seeds its geometry and checks
     non-overlap in code (`python/references/lifecycle-seeding.md`,
     "Demo data").
   - Ready for both front doors: a `User` type, and a `description=`
     on every method, written for the AI. A description can't be
     edited once deployed; `mcp=` can
     (`python/references/api-schema-evolution.md`).
   - The look: the five-line brief (who and on what screen, the task,
     the primary view's question, the accent and its real source or
     "house default, no brand supplied", the type) and the primary
     view for the task (`web-app/references/ui-design.md`, 01–02).
     Light and dark both designed; web-app: a toggle in the first
     build; mcp-ui: the host's theme (`mcp-ui/references/ui-design.md`).
   - mcp-ui: the `User` type and its methods, which methods get
     `UI()`, the AI's tool surface, about three example prompts, most
     ending on a turn that renders a `UI()`.
   - web-app: the pages and the methods each calls.
5. Write the design to `design/design.md` as it is stated, in the same
   words the user reads: every choice with its why, the deviations
   from the brief, the alternatives set aside. Keep it current until
   accepted; it outlives the conversation.
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
  route, plus a one-clause domain reason ("grows without bound, so it
  paginates"; "logged-in users only, because the document is
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

1. **Application types: decompose aggressively.** Every entity the
   user adds, edits, lists or finds over time is its own `Type` with
   its own state, even when each user has few. One parent holding
   `list[Person]` flattens N actors, blocks per-entity auth and methods
   and forces a rewrite as it grows. A collection synced from an
   external system is unbounded by definition. Items one action must
   change all or none ("hold these 4 seats") stay inline on one actor,
   the lock (`python/references/state-collections.md`, Step 1 and its
   counter-test).
2. **`User`: always.** The MCP front door and the owner of per-user
   state in the web app; creation routes through it in both. It holds
   identity and the IDs of what it owns; auth, persona, engine config
   and caches are their own Types
   (`python/references/state-actor-decomposition.md`).
3. **Container shape per collection.** The parent stores references,
   not objects: `list[Model]` for bounded sub-records with no identity,
   `list[str]` of IDs for a bounded entity collection read whole,
   `OrderedMap` for anything unbounded, paginated or externally
   synced. A cap added to make a collection bounded proves it unbounded
   (`state-collections.md`, Step 2).
4. **Creation.** A `Transaction` on the owner calls
   `<Type>.create(context)` and registers the ID in the owner's
   container; the type's constructor is a `create` Writer with
   `factory=True`.
5. **State shape.** Every field has `Field(tag=N)`, a zero-value
   default and `description=`; a nested `Model` owned 1:1 is
   `Optional[X] = Field(tag=N, default=None)`, hydrated in `create`
   (`python/references/api-pydantic.md`; mcp-ui also
   `mcp-ui/references/api-state-shapes.md`).
6. **Method type.** `Reader`: read-only. `Writer`: one state.
   `Transaction`: more than one state instance. `Workflow`: long-running
   control flow and every external-service call.
7. **Identity.** A singleton created in `initialize`, or many with
   their own IDs?
8. **Stdlib before your own types.** `Queue`, `OrderedMap`, `Presence`,
   `Topic`, `Item`, `OAuthTokenManager`, `Ciphertext`: never a `Model`
   with one of those names. Each is registered in
   `servicers/registry.py` with its `servicers()` and `_library()`;
   a missing one fails the first call with an unknown state type, a
   missing library fails startup.
9. **Backend LLM calls** use `reboot.agents.pydantic_ai.Agent`, never a
   raw provider SDK or a bare `pydantic_ai.Agent`, which re-bills on
   every replay (`python/references/agent-pydantic-ai.md`).
10. **Front-door surface.** mcp-ui: `mcp=Tool()` or `mcp=None` per
    method; a `UI()` on the entity's own `Type` when the AI passes its
    ID, on `User` when it is about the user (mcp-ui skill, "UI
    Placement"). web-app: the pages and the methods each calls.

### When Correct Decomposition Fights the UI

One hook on one actor tempts a flattened `list[Item]`. The data model
wins: one actor per item, an `OrderedMap` index on the parent, and a
composing reader on the parent that ranges one page of IDs, reads each
item and returns hydrated items with a `next_cursor`; the page
subscribes to it. mcp-ui: `mcp-ui/references/react-app-tsx.md`;
web-app: `python/references/patterns-cross-actor-reads.md`.

## Step-by-Step Build Flow

**Run all commands from the application directory**; before each step,
read its front-door reading list. The design, the feature files and the
API file are written into the bare folder; the template arrives at Step
2, after them. Step 1 closes the first prototype's
design; its acceptance comes with the running prototype (Step 7), and
from then on "Accept the Design" sits before each feature's
implementation.

**The first prototype is the whole design, built straight through and
said as it goes.** Steps 1 to 7 build every feature file's model,
methods, pages or tools and scenarios. Each step's narration names
the object, method or file being written and the decision behind it,
in the user's nouns, in two or three sentences before each tool call
or group of calls; a step past ten minutes says what takes the time
and what it would cut. The first prototype skips the screenshot pass
and page timing (Step 5); they come with the first update.

**Teach as you build, design first.** The first build is the user's
first look at Reboot, and the design is what it teaches most. Each
design decision says which of the welcome's three questions it answers
and the principle behind the answer, in the user's nouns: "A
reservation is its own object, because it lives and changes apart from
the room" (what are the objects); "`book` is a transaction, because it
holds every night or none" (what can it do); "only the app calls
`hold`, so no guest can claim a night directly" (who may call it). The
first map says its columns are those three questions. Later steps add
one or two sentences on the idea each rests on, never a lecture. Step 1:
a state type is an actor, its state kept by Reboot and its methods run
one at a time, so two guests cannot book the same night; a reader,
writer, transaction or workflow is what a method may touch. Steps 2a
and 6: a scenario is the rule in English that the suite runs. Step 4:
an authorizer is who may call each method, enforced in production.
Step 7: the dev loop restarts on every edit, the dashboard shows the
model and the features, `rbt inspect` reads what is stored. A term the
user asks about gets the reference's answer, in their words.

**Once Step 1 has written the API file, start the developer
dashboard** ([`dashboard` skill](../dashboard/SKILL.md)): it opens on
its Models page with the model to show, and its Features page has the
feature files. Started earlier, it opens on "Waiting for your API".
When it opens, say what the user is looking at: the Models page shows
each object, its state and its methods, the map's first two questions.
The Call Graph, which method calls which, stays empty until Step 3
writes the methods' code, then fills in. If it fails, say so in a
sentence and keep building.

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

For the first prototype this is the handoff (Step 7): the user reviews
the architecture, the rules and the feature set on the running app,
the assumptions beside it. For every later feature it comes before the
implementation, once the feature's slice is on screen. The first time,
open with the card (`references/flywheel.md`, "Stage cards") and the
**review table**, one row per rule, in the design's words:

| State type | State ID | Rule | Method | Kind | Who may call | Scenario |
| --- | --- | --- | --- | --- | --- | --- |
| `Room` | hotel and room number | booked at most once per night | `book` | Writer | the app itself (from `Reservation.create`) | "A second guest requests a booked room" |

Every rule in a feature file gets a row; a rule with no owner, method
or scenario is a gap to name, not to fill silently. List the feature
files by path and the assumptions as made, and point at the
dashboard's Models and Features pages. Under the table, **Beyond the
brief**: one line per interaction, rule or status the design adds to
or changes from the brief, with its reason; `design/review.md` records
the answer to each. Beside it, the five-line brief and, with no brand
supplied, the offer of the house default or a brand or site to read.
Then the ask, in one line (`references/flywheel.md`, "The ask, in one
line").

**After the review.** A change goes back to its slice, the feature
skill or the design, then here again; a changed assumption is rebuilt
into the prototype before the next feature. A later feature waits for
the user's agreement unless they said up front to build on, and then
the record says which slices were not accepted.

Once accepted, the repository records it (Step 2, item 5): the design
in `design/design.md`, the review table in `design/review.md`, an entry
in `design/decisions.md`, the record `scripts/model_diff.py --accept`
writes in `design/accepted.json`, and one commit holding them with
`api/` and the feature files, the base every later model diff measures
from.

### Step 2 — Project shell

Read "Before the project shell". Copy `templates/<front-door>/` with
its `copy.sh --merge` (see [`templates/README.md`](templates/README.md));
never retype a scaffold file from memory. `--merge` fills the
placeholders, renames paths, keeps every file the project already has
(step 1's API file, a `CLAUDE.md`) and replaces the dashboard's three
stubs (the dashboard keeps running). The sample servicer, feature, test
module and UI are replaced in steps 3, 5 and 6; a dual-frontend app
copies `templates/both/`. Then say what the folder now holds, directory
by directory, each with its job in the user's terms, from the table in
`templates/README.md`: `api/`, the objects and their methods, the one
definition the backend and the browser are generated from; `backend/src/`,
the code behind each method; `tests/`, the feature files and the
scenarios that run them; the frontend directory, the pages; `scripts/`,
the test, deploy and backup commands; `deploy/`, the deploy's settings
and record; `AGENTS.md`, the project's map for a coding agent. From
here on, a step that adds a file names it and its job the moment it
lands. Then:

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
5. **Record the design.** `design/design.md` is the design as assumed
   (Design Phase, item 5). Write `design/review.md` (the review table,
   the feature files by path) and the first entry in
   `design/decisions.md` (below), and commit `api/`, `tests/*.feature`
   and `design/` with the scaffold as `Design assumed: <title>`, the
   project's first commit. When the user accepts at the first handoff
   (Step 7), run `python3 scripts/model_diff.py --accept`, add the
   entry, and commit as `Design accepted: <title>`: that commit is the
   base every later `model_diff.py` measures from, and what the pull
   request and the release record mean by "accepted". Built without
   stopping, the record stays marked not accepted.

   `design/decisions.md` is a log, newest entry last, never rewritten:
   each acceptance adds one entry with what was decided and why
   ([`references/flywheel.md`](references/flywheel.md), "The decisions
   log").

### Step 2a — Run the scenarios red

Before any servicer body: read "Before the authorizers" (Step 4's
list), then declare every servicer class with each method raising
`NotImplementedError` and its real `authorizer()` (the test harness
denies every call to a servicer without one, so a run without them
fails on `PermissionDenied` and proves nothing), register them in
`servicers/registry.py`, and run the design's scenarios
(`scripts/test.sh full`). Each must fail for the reason its own
words name, the [`feature` skill](../feature/SKILL.md)'s Step 2a; a
step not found or a fixture that never started proves nothing.
`scripts/model_diff.py` reports whether a run has happened since
acceptance, so the handoff shows it. Then Step 3, one servicer at a
time, each scenario going green.

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

Read "Before the authorizers" (done at Step 2a). **Every servicer has
carried a real `authorizer()` since its stub; review each against the
rules below**: `rbt dev` only logs
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
   then, after the review, `uv run --with playwright python scripts/screenshots.py <routes>` saves every
   route at desktop and phone width, light and dark; open and check each
   against `ui-design.md` principles 03–09 and its Never list, fix
   what fails in one pass, then pin it with a look scenario per page.
6. **Responsive to the person, by Google's "good" thresholds**
   (Core Web Vitals, and RAIL for input):
   - **Loads:** a page's content, the data and not its skeleton, on
     screen within 2.5 s (LCP's threshold), and the layout steady as it
     arrives (CLS ≤ 0.1: skeletons shaped like the content).
   - **Input:** every click and keypress answered within 100 ms, the
     next frame ideally (RAIL; INP's threshold is 200 ms): the button
     shows its pending state at once, the result follows. Never block
     a handler on work the person didn't ask to wait for.

   After the review, time the loads on every route, cold and warm, against the local
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

Read "Before the tests". **Write and run every feature's scenarios
before handoff** (the first prototype's all; later, each feature's as
it is built), in the built-in steps of
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

Run `scripts/test.sh full`, then `uv run mypy backend/ tests/` from the
project root (config: `python/references/lifecycle-project-setup.md`);
proceed only when every scenario passes (or is `@blocked`) and mypy is
green. Each scenario boots the app, so the suite takes minutes: run it
in the foreground with the tool's longest timeout (600000 ms in Claude
Code) and wait for the result; past about 40 scenarios, iterate one
area at a time (`scripts/test.sh <area>`) and run `full` once before
handoff. Never leave it in the background and end your turn: nothing
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

**Hand off** only after the final test run has finished, with the
prototype committed as `Prototype: <title>` (a deploy refuses a dirty
tree). The first time, this is the review ("Accept the Design"). Open with the prototype
card ([`references/flywheel.md`](references/flywheel.md), "Stage
cards"), then:

1. The app's URL (mcp-ui: the setup wizard's; web-app: the page's).
2. The result: scenarios passed, anything `@blocked` and why, mypy
   clean, each route's load against the thresholds (Step 5) with any
   still over and its cause.
3. The assumptions as made (Design Phase, item 0), and every deviation
   from the brief or from the plan's own specs, with its reason (item
   2); the first time, the review table, Beyond the brief and the look
   ("Accept the Design"), and the ask last.
4. The state types and methods as built, one line each (Step 1), when
   they changed after the design; and whether the design was accepted
   ("Accept the Design"), as `python3 scripts/model_diff.py` says. A
   pull request, when the developer wants one, has the body in
   [`references/evidence.md`](references/evidence.md); `prove.yml`
   posts the evidence on it.
5. `AGENTS.md` current (Step 2.4), and the `FINDINGS.md` items added;
   when there are any, offer the [`report` skill](../report/SKILL.md).
6. Unless the user asked for only one front door, the one-line offer of
   the other (`app` skill, "At handoff").
7. What to add next, proposed; the user picks.

## Update Flow

A feature after the review comes here one at a time: agreed, sliced,
built, run and handed off, before the next.

1. Read `.rbtrc`, `design/design.md` and `design/decisions.md`, the
   API definition, servicer, `main.py` and the frontend entry (mcp-ui:
   `frontend/mcp/<ui-name>/App.tsx`; web-app: `web/src/App.tsx`). A
   change that goes against a recorded decision says so to the user
   before the design changes, naming the entry and its why. Work on
   `main` or a branch as the developer chose
   ([`references/flywheel.md`](references/flywheel.md), "Where the work
   happens").
2. Assess state model changes; with persisted state or a deploy, follow
   `python/references/api-schema-evolution.md`.
3. Agree on the feature in English and write its `@wip` feature file
   before the API changes ([`feature` skill](../feature/SKILL.md)),
   then show the slice of the model it adds, as review-table rows.
4. Update the API (every new property with `description=`) →
   `uv run rbt generate`. Tell the user any state type or method added
   or changed, one line each (Step 1). Run
   `python3 scripts/model_diff.py` (it measures from the accepted
   design; `HEAD` as the base when the project has no record): any
   design change goes through "Accept the Design" before step 5, with
   `design/design.md` updated to the changed design. Once accepted,
   `design/review.md` rewritten for it, a new entry at the end of
   `design/decisions.md` (Step 2.5; **Replaces** names the entries it
   overturns, which stay as they are), `python3 scripts/model_diff.py
   --accept` and a commit of `api/`, `tests/*.feature` and `design/`
   ("Design accepted: <what>") record it. None (a new scenario under an
   existing rule, a code fix) stays in Prove.
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
  would load React twice). Delete `web/`. The SPA now serves under
  `/__/frontend/web/`, where a deep link to a path route 404s: switch
  the router to hash routes (`#/kind/id`; plugin-browser, 1.6.0).
- To an MCP UI: copy `both/frontend/web/`, and fill `__Title__` and
  `__Initial__` in its `index.html`.
Then switch the AI's methods to `mcp=Tool()`, add any `UI()` methods,
write the new front door's scenarios, and take `AGENTS.md`'s
frontend rows from `templates/both/AGENTS.md`.
