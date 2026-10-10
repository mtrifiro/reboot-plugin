---
title: "Findings into the plugin: the ingestion strategy"
summary: "Match each finding to the cheapest mechanism that holds (row, template, check, shim, prose, eval), in five waves."
kind: report
audience: maintainer
---

# Findings into the plugin: the ingestion strategy

Written 2026-10-10 from a read of every numbered finding in
`~/projects/reboot-findings` (328) against the corpus in `findings/`
(558 items), the skills as they are on `ia-restructure`, the templates,
the shims and the reading budget. It says where the backlog stands, which
mechanism each kind of finding should land in, what the pipeline needs
so the next import is cheaper than this one, and the concrete work in
five waves.

## 1. Where things stand

**The corpus.** 361 of the 558 items target the plugin. 262 are
`Resolved` (a skill section documents the problem, often as a workaround;
Reboot may still have the bug), 86 are `Open` (60 distinct gaps after
duplicates), 13 `Obsolete`. The rest target the framework (66),
reboot.bdd (22), the primer (19), the Cloud (4) or record something that
worked (86).

**The numbered view** (`reboot-findings`, where the hand-written `fixes`
field is the real backlog):

| Set | Findings | Meaning |
| --- | ---: | --- |
| A Skills or App fix still listed | 94 | 85 want a skill change; 9 list only App or Reboot fixes (`A.3`, `A.5`, `A.8`, `A.9`, `A.11`, `A.12`, `A.13`, `A.14`, `P2.15`) and belong to the CRM, except `A.14` (wave 1, item 11) |
| Open in the corpus, only a Reboot fix listed | 27 | 21 of them carry a workaround that belongs in a reference |
| Covered, only a Reboot fix left | 113 | the upstream list; the workaround is documented |
| Covered, nothing left | 94 | done |

The board: 64 findings `Reported`, 264 `New`.

**The budget is managed.** When this was written the three minimal
reading paths sat at their ceilings: MCP UI 38,879 of 39,000 words,
Web App 38,480 of 38,500, backend-only 25,803 of 26,000, so a sentence
added to `build/SKILL.md` or to a reference every build reads had to be
paid for by a cut of the same size. The same day the ceilings became a
managed budget (section 3f): raised to 40,500, 40,000 and 27,000 as a
recorded allowance for the prose in wave 3, with the findings it is for
and the signal that judges it kept in `tools/budget.py`. Words are still
accounted for: prose that fails its signal moves into a mechanism and
comes back out, and prose outside the minimal path (a conditional
reference) stays free. That still shapes everything below.

**Most open items are real.** A probe of 55 key phrases from the open
items against today's files found about one in eight already covered
(the `StateNotConstructed`-on-read family in `rpc-refs.md`, `expunge
--yes` in `stop-restart-reset.md`, restyling in `ui-design.md`). The rest
are genuinely absent.

**The same things keep coming back.** 92 findings carry an "Also seen
in other projects" block and 163 corpus items are duplicates. A reader on
an unconstructed actor aborting `StateNotConstructed` appears in ten
numbered findings from more than a dozen projects across 1.4.1 to 1.6.0;
roles keyed by email with no `email_verified` in two builds of the same
brief; port collisions in seven projects; an action step after `Then`
in three. A repeat after the prose landed is the clearest signal
that prose was the wrong mechanism.

## 2. The principle: match the mechanism to the failure

A finding is a moment where an agent stalled. The fix that holds is the
one that reaches the agent at that moment, at the lowest cost to its
context. Seven mechanisms, from cheapest to the agent to most expensive;
each has a precedent in this repo.

| | Mechanism | Fits when | Reading cost | Precedent |
| --- | --- | --- | --- | --- |
| M0 | Upstream issue (`Reboot:` fix) and `known-defects.json` | Reboot has the bug; the plugin can only work around it | none | `tool-checks-01`, the `report` skill |
| M1 | Error row (`## Errors you will see`, generated into `errors.md`) | the agent will be holding an error string | none: `errors.md` is `step: any`, grepped on demand, and the reminder hook says to grep it | the 225-row index |
| M2 | Template file (the fix ships in the project) | a scaffold or config fact: ports, env files, tsconfig, deps, fixtures, scripts | none | `registry.py` (A.6), `AGENTS.md` (A.1), `deploy.sh` setting `DOCKER_HOST` (P1.3), `strictPort` (P3.65) |
| M3 | Shipped check (fails before the slow thing, with the fix in the message) | the agent only finds out after minutes: a suite run, a generate, a deploy | none, and it **replaces** prose | `tests/step_order.py` (P3.188), `model_diff.py`, `api_removals.py`, `backup.sh` refusing an empty export |
| M4 | Plugin hook or shim (every project, every session) | machine and process traps: orphans, the RocksDB LOCK, a missing tty, venv patches, a port another cwd owns | none | `orphans.sh` (P2.47, P1.9), the schema guard (P1.4, P3.43), `own.sh`, the vendored `reboot-std-oauth` (P1.22) |
| M5 | Plugin check (`tools/`) | the skills could drift from the pinned Reboot or from each other | none | `check-symbols.py` + `known-defects.json`, `check-cli.py`, `check-facts.py`, `templates-drift.py` |
| M6 | Reference prose (Do this / Never / Limits / Scales as) | a design rule the agent must hold before writing | counts on the minimal path unless the reference has a `when:` | the 4.1 cluster, 113 items |
| M7 | Eval grader | a design-phase rule that prose failed to hold | none at build time; model calls when run | `design-roles`, the gate evals |

Rules that follow:

1. **Anything with an error string gets an M1 row**, whatever else it
   gets. 162 corpus items are tagged `error-text`; 25 of the open plugin
   items are. Rows cost nothing and hit exactly when the agent is stuck.
2. **A repeat sighting escalates one rung.** Prose that was there when a
   second project hit the same thing moves to a check, a template file or
   a shim. P3.188 is the model: the Errors clause was deleted when
   `step_order.py` shipped.
3. **A check that ships deletes the prose it replaces.** That is how the
   budget comes back.
4. **Prose on the minimal path is accounted for.** It draws on the
   allowance recorded in `budget.py` (section 3f), which names the
   findings it is for and the signal that judges it; `budget.py --check`
   holds the ceiling. Prose in a conditional reference (`when:`) is
   outside the path and free: 31 of the 68 python references are
   conditional, and a new reference can be.
5. **A Reboot-only finding still gets its workaround written down**, as
   a row or a Never, until a probe says the bug is gone.
6. **Primer and app items leave the plugin backlog.** The primer ones go
   the way `flywheel-primer-fixes.md` went; the CRM ones are retargeted.

## 3. Pipeline changes, so the next import is cheaper

The pipeline exists (project `FINDINGS.md` → corpus → `build.py` numbers
→ `split.py` files → `workarounds.json` → `resolved_by`). Five things are
missing from it.

**a. Re-judge the open set once.** The 86 open plugin items were judged
at import; about a dozen are covered now. One session, item by item,
against the file each names; flip them with a `resolved_by`. Fix the one
schema error `tools/findings.py` reports today (`restaurant-app-3-01`
is `Open` while its canonical `reboot-crm-26` is `Resolved`).

**b. Let `resolved_by` name a mechanism.** Today it must be a heading
under `skills/`, so a finding closed by `step_order.py` has to point at
an Errors table and explain itself in a "Resolution" paragraph.
`findings.py` should accept a path under `skills/build/templates/`,
`hooks/`, `hooks-handlers/`, `bin/`, `lib/`, `tools/` or `evals/` (the
file must exist; `§` names a heading, function or grader), and a new
`mechanism:` field (`row | template | check | hook | shim | tool | prose
| eval`). Then `findings.py` and the Plugin Browser can say how strongly
each item is covered, and rule 2 above becomes a query.

**c. Make repeats visible.** A duplicate carries its canonical's status,
so a re-sighting of a `Resolved` item is silent (that is exactly the
schema error in a). `split.py` already folds sightings; have it write
`sightings: N` and `last_seen: <version>` on the numbered finding, and
have the importer reopen a canonical (`status: Open`, with the new
sighting) when a project reports it again after its `resolved_by` landed.
That is the escalation trigger.

**d. `findings.py --todo`.** Join the open corpus items with the
`fixes` lists in `reboot-findings` through `corpus_index.json` and print
the Skills fixes grouped by the file they name, with the mechanism rule 1
and 2 suggest. The list in section 4 was built by hand; this makes it a
command.

**e. Probes for the defects we work around.** For each framework defect
with a three-line repro, a script under `tools/probes/` that asserts the
bug is still there against the pinned Reboot, run by `check-all.sh
--full`. When a probe fails (the bug is gone), the check fails until the
`known-defects.json` entry, the workaround row and the venv patch are
removed. First candidates, all with repros in the findings: P1.8
(`schedule(when=)` from a workflow), P3.13 (a plain `def` callback to
`.write()`), P3.31 (`Queue.empty` before any enqueue), P4.2 (`search` on
an unconstructed `OrderedMap`), P3.18 (`default_factory` on a nested
model), P1.4 (a `description=` edit refused at boot), P3.28 (a `bytes`
field). This is the only way the budget shrinks on an upgrade instead of
growing.

**f. The managed budget.** Decided 2026-10-10; it replaces the ceilings
that only moved down. Three rules, kept in `tools/budget.py`
(`--ceilings` prints the record):

- A cut lowers a ceiling, as before, and names what moved into a
  mechanism.
- A raise is a record: the new number, the date, the findings the words
  are for, and the signal that will show whether they earned their
  place. The signal is no re-sighting of those findings in a project
  built after the words landed (3c makes that visible) plus the graders
  that cover them (wave 4). A raise with no signal is refused in review.
- Words whose signal fails are condensed: the rule moves to a mechanism
  (a row, a template file, a check) and the prose comes out;
  `check-facts.py` proves the cut dropped no fact.

The first record raises the ceilings to 40,500 (MCP UI), 40,000 (Web
App) and 27,000 (backend-only) for wave 3: about 1,000 words on the
widest path, plus a reserve. The findings each path's allowance is for
are listed in the record, so a raise is judged finding by finding, not
as a lump.

## 4. The work, in five waves

Ordered by severity, sightings and cost. Each wave 1 item is one small
commit with a test, as `tests/templates/step_order_test.py` is for
P3.188. Finding numbers are from `reboot-findings`.

### Wave 1: zero-budget mechanisms (templates, checks, shims)

1. **Ports at scaffold** (P3.139, P4.29, P3.171, P3.185; five projects).
   `copy.sh` picks three free ports and writes `.rbtrc` (`dev run
   --port`, `--dashboard-port`, `dashboard --port`), `vite.config.ts`,
   `web/.env.development` and, for `both`, the missing
   `frontend/web/.env.development`, and `allowed_origins`. Before trusting
   a port that answers, the `run` and `dashboard` steps check the owner's
   cwd (`lsof`); the band reads the dashboard port from `.rbtrc` (P4.28).
2. **Suite timeouts and split runs** (P1.10, P1.10c, P3.193, P3.196).
   `pytest-timeout` in the dev group with a per-file budget; a
   `scripts/test.sh` with `changed | <area> | smoke | full`; `last_run.py`
   records the tested tree's hash; a pre-push hook for `Workflow: main`
   projects; build Step 6 gives the number to pass (600000 ms) in one
   line.
3. **An API lint before `rbt generate`** (`scripts/api_lint.py`, run by
   the `rbt` shim on `generate` and by `prove.yml`): reserved method
   names (P4.24, P3.95), Python 3.10 syntax and quoted forward references
   (P3.165), a `Model` referenced across packages (P1.16, P3.180), a
   growing `list` on a singleton type (P2.48), `bytes` fields (P3.28),
   field-less error models (P3.125), a factory constructor declared as a
   `Writer` (P1.6, P3.175). Every message names the fix and the reference.
   Precedent: `api_removals.py`.
4. **A feature lint** (grow `step_order.py` into `feature_lint.py`):
   a `Rule:` with no `Scenario:` (P3.137), `with` clauses after the actor
   (P4.31), a quoted `<name>` that matches a saved value (P0.6), a
   backtick inside a quoted value (P3.178). All before the first step
   runs, with the line and the fix.
5. **Harness hygiene in `conftest.py`** (P1.18, P3.33, P3.146): bind
   test servers to `127.0.0.1`; the `web_app` fixture reports the
   requests still open on a navigation timeout; an `ANTHROPIC_API_KEY`
   placeholder when `pydantic_ai` is importable.
6. **`rbt` shim guards** (P3.17, P3.50, P3.39, P3.145, P4.1, P3.163,
   P3.138): `expunge` with no `--yes` and no tty exits with the message
   instead of blocking; `expunge` while the RocksDB LOCK is held is
   refused; `dev run` while the LOCK is held waits briefly, then names
   the holder; a project with a `.rbtrc` and a `.venv/bin/rbt` runs that
   one, so `rbt` and `uv run rbt` agree; the shim resolves its own path
   through symlinks and names the missing file when `lib/` is not beside
   it.
7. **Known-defect patches applied by the `uv` shim** (P1.2 `ENOBUFS`
   in `protoc_gen_es_with_deps.cjs`, P1.1 LuaJIT on macOS arm64, P1.22
   the vendored oauth module, P3.176 the namespace-package lookup): one
   idempotent `lib/patch_reboot.py`, keyed by `known-defects.json`, run
   after `uv sync` and on first `run`; each entry names the finding and
   the version that removes it. The most invasive item here; the
   precedent is vendoring `reboot-std-oauth`, and reboot-crm and new-crm
   already apply these by hand. **Needs a decision.**
8. **Dashboard heap and orphans** (P1.12, P3.127, P2.47): the shim sets
   `NODE_OPTIONS=--max-old-space-size=12288` for `rbt dashboard` when
   unset; `orphans.sh` reports `langserver.index.js` orphans.
9. **Web template type-check** (P3.170, P3.51): a `typecheck` script
   running `tsc -b`, `exclude: ["src/api"]` in `tsconfig.app.json`, the
   `@bufbuild/protobuf` peer named.
10. **Red run before servicers** (P3.192): `model_diff.py` or the band
    flags a servicer commit when `tests/.last-run.json` has no run for the
    accepted features; Step 2a becomes a numbered step (a restructure, not
    an addition).
11. **A suite-running guard and a doctor script** (A.14, P3.169, P3.39,
    P3.156, P3.73): `last_run.py` keeps a sentinel while the suite runs,
    and the plugin's PreToolUse hook refuses `rbt generate`, `rbt dev run`
    and edits under `backend/` while it exists, as the schema guard
    refuses incompatible API edits; a `scripts/doctor.sh` runs the
    rule-out-local-causes list (orphans, the LOCK holder, the watcher
    alive, `ALLOWED_*` variables, a second suite, both IP stacks) before
    anyone blames the framework.
12. **Screenshots after the readers deliver** (P3.201): `scripts/screenshots.py`
    waits for the skeletons to clear and for the card fade before it
    captures.

On 2026-10-10, as wave 1 was being built, restaurant-app-2's seven
items arrived (P3.197 to P3.201, P4.35, and a worked-well note). P3.201
went into wave 1 above; the look items are in waves 3 and 4.

**Wave 1 status, 2026-10-10.** Landed, each with a test under `tests/`
and all three templates building and passing their scenarios: items 1
(ports, with `copy.sh --ports` for the dashboard skill), 2 (timeouts,
`scripts/test.sh`, the tree hash, `.githooks/pre-push`), 3 (the API
lint; the `Writer(factory=True)` check is a note, since the templates'
own sample is one), 6 (the `rbt` shim's guards, the project venv, every
shim symlink-safe and naming a missing `lib/`), 8 (the dashboard heap
from both shims; `orphans.sh` names pyright's orphan), 9 (`typecheck`;
the `src/api` exclude was dropped, since `tsc` checks imported files
either way), 10's `model_diff.py` line on runs since acceptance, 11
(`hooks/suite-guard.sh`, `scripts/doctor.sh`) and 12. Seventeen corpus
items moved to Resolved with a Resolution paragraph each. Still open:
items 4 and 5 and the build skill's Step 2a renumbering and Step 6
timeout number (P3.192, P3.193), which edit files the other session has
in flight (`step_order.py`, `conftest.py`, `build/SKILL.md`); item 7,
pending the venv-patching decision; and `reboot-findings`' hand-written
`fixes` lists, which live in the other repository.

### Wave 2: error rows, one session

Every open `error-text` item and every open Reboot-only item with a
workaround becomes a row in its owning reference's Errors table;
`gen-index.py` regenerates `errors.md`. Among them: `issubclass() arg 1
must be a class` (P3.165); `is reserved` for any name (P4.24); `cannot
encode field … to JSON` (P3.141); `badly formed hexadecimal UUID string`
(P3.158); `Unknown` wrapping `StateNotConstructed` through a transaction
(P3.149); the `Participant/Prepare` loop after a mid-commit kill
(P3.143); `ResetAborted: 'Unavailable'` after `kill -9` (P3.155);
`ContravariantStateType` (P3.191); `AssertionError: Transaction …
missing` (P3.89); `spawnSync /bin/sh ENOBUFS` (P1.2); `database.cc:1374
Check failed: inserted` (P2.11, P2.7); `Page.goto: Timeout 30000ms`
(P3.33); `must be JSON` for a recall inside JSON5 (P3.177); `Cannot set
properties of undefined` from a second reader hook (P3.161); the
sequential-seed `presumed deadlocked` warnings (P2.45); `Error in
sys.excepthook` (P3.87); the `/develop/side_effects` 404 (P3.104); the
whoami CORS error (P3.41, P3.129); `Connector not found` (P3.182); the
Vite cold-start `TimeoutError` (P3.179).

### Wave 3: prose, on the record

By file. "Free" means the reference is conditional or `step: any`, so
it is outside the minimal path; "paid" means the words draw on the
allowance recorded in `budget.py` against the findings named there
(section 3f).

- **`auth-claims.md`** (free; `when: claims`): request `email_verified`
  in the Do-this example, check it in the `set_claims` example, a Never
  against linking an email-keyed record on an unverified address (P1.24,
  red, two builds); the allowlist boot guard (P3.168).
- **New `auth-roles.md`** (free; `when: "staff sign in with roles"`):
  the worked roster shape from reboot-crm's `servicers/auth.py` and
  `Team.register`: one roster actor, `my_role` and `role_of`, access
  versus role gates and their per-call cost, invitations by verified
  email, the first admin, one feature file (P3.190, P2.31, P3.59, P3.167,
  P3.166). The design phase points at it when a brief says staff sign in.
- **`react-generated-client.md` and `react-client.md`** (paid; the two
  most-named open files): one Limits and Never pass: a socket per bare
  handle (P2.43), the four browser traps (P3.38), int64 as `number`
  (P3.141), `httpCall` shapes under `.items` (P3.151), UUID idempotency
  keys (P3.158), the six-connection ceiling (P4.34), sign-in without a
  `User` type (P3.94). Consolidating the two files' overlap can make this
  net zero.
- **`servicer-authorizer.md`, `auth-custom-predicates.md`,
  `servicer-reader.md`, `lifecycle-initialize-hook.md`** (paid; on the
  servicer and auth steps of every path): a predicate reads its `state`
  argument and never calls a reader on its own actor (P3.166); a
  fan-out that faces a client or an MCP host checks its own caller first
  (P3.167); the `Any` plus `isinstance` predicate form (P3.191) and the
  pointer to `auth-roles.md`; an aggregating reader sees other actors as
  of its host's last write (P3.153); when `initialize`'s idempotency
  scope stops covering a prior boot's create (P3.102).
- **`servicer-transaction.md`** (free): participants are the lock set;
  aggregators out, written after commit (P2.41, P3.149).
- **`servicer-workflow*.md`** (free): an `.always()` result never feeds
  a memoized call (P3.144); validation can re-submit a `per_workflow`
  transaction after completion (P3.152); drive post-commit phases from
  committed state (P3.154); the durable backoff pattern (P3.147).
- **`rpc-refs.md`**: already says a reader on a missing actor aborts;
  flip P3.66, P3.120, P3.128 and the duplicates; add the
  `MixedContextsError` rule beside `ref()` if still absent.
- **`patterns-cross-actor-reads.md`** (free): an `OrderedMap` hop inside
  a fan-out (P2.46); period-keyed aggregates and the zero-value reader
  (P3.195).
- **`stdlib-ordered-map.md`** (free): `insert` replaces (P4.30); `range`
  on a never-inserted map aborts (P3.120); one registration answer in all
  three files (P4.33).
- **`api-schema-evolution.md`** (free): stored enum values, singleton
  ids, no actor delete (P3.164).
- **`lifecycle-dockerfile.md`** (free): the Cloud image is Python 3.10
  (P3.165). **`lifecycle-dev-loop.md`** (free): a reload per save
  (P3.162). **`scheduling-basic.md`** (free): can `schedule()` target a
  transaction (P3.105); the restart crash loop (P2.11).
- **`build/SKILL.md`** (paid, every path): where History events live,
  one sentence linking `state-collections.md` § Scales as (P2.48); the
  "Beyond the brief" section on the Accept card, recorded in
  `design/review.md` (P3.194); hash routes for a `both` SPA (P3.186).
  Pay with cuts from the same file.
- **`feature/SKILL.md`** (paid): a batch-agreement path for large
  feature lists (P3.174).
- **`mcp-ui/SKILL.md`** (paid): a signed-in app's view cannot make
  live calls from claude.ai and the `UI(request=<Model>)` alternative
  (P1.23, red); reconnect after a deploy that changes tools (P4.26). The
  rest go to `api-method-types.md` and `api-state-shapes.md` (paid, api
  step) as rows or one line each: the frozen tool description (P4.25),
  what a workflow tool returns (P4.27), `useMcpToolData()` (P4.32),
  hydrate in a factory `Transaction` (P3.175).
- **`deploy/SKILL.md`, `lifecycle-reboot-cloud.md`, `inspect/SKILL.md`**
  (net zero): the printed port-443 URL replaces every `:9991` (P3.172);
  republish the frontend in the same deploy as a breaking change
  (P3.173).
- **`run`, `dashboard`**: Known issues rows, not prose (P2.47, P3.143,
  P2.42); they feed `errors.md`.
- **`ui-design.md` and the Accept card** (paid; restaurant-app-2's
  review of its 2026-10-06 build): the five-line visual brief on the
  Accept the Design card with the no-brand offer (P3.197); a product the
  user names is read from its site, never from memory (P3.198); a loop
  for a look change on a running app, with rendered candidates after a
  second rejection (P3.199); rules for a spatial hero view and a
  demo-data item for spatial domains (P3.200).
- **`testing-features.md`** (free-ish): recalls cannot sit inside a
  JSON5 literal (P3.177); the claims sign-in custom step beside the
  built-in (P3.189); clause order (P4.31).
- **Leave the plugin**: P2.15, P2.28, P2.29, P3.71, P3.99, P3.100,
  P3.101, P4.20 (primer); A.3, A.5, A.8, A.9, A.11, A.12, A.13 (the
  CRM).

### Wave 4: evals for the rules prose failed to hold

Add graders to cases that exist: `design-roles` gets `email-verified`
(P1.24) and `roster` (P3.190); `design-ready-for-both` or a new
`design-history` checks that History events sit on short-lived entities
(P2.48); `design-accept-gate` checks for a "Beyond the brief" section
(P3.194) and for the visual brief (P3.197). A rendered check is the
one kind no eval has: a judged rubric over the class page
`tools/style-check.py --browser` renders, and the screenshot review as
an artifact in the handoff (P4.35). The red-run rule (P3.192) cannot be an eval (runs are
read-only); it is wave 1 item 10.

### Wave 5: upstream and obsolescence, ongoing

The probes from section 3e, one per upgrade cycle; `known-defects.json`
grows from one entry to the set that is patched or probed. The 113
covered Reboot-only findings are the `report` skill's queue, at the
user's pace; the 21 open ones get their workaround row in wave 2 first.

## 5. What not to do

- Don't add a sentence to a SKILL.md for something a check can catch at
  the moment it happens.
- Don't bulk-flip statuses; each `resolved_by` must name a section or
  mechanism that exists, as `findings.py --check` enforces.
- Don't write findings into the corpus by hand; they come from a
  project's `FINDINGS.md` through the importer (`REPORTING.md`).
- Don't ship a mechanism that explains itself only in `findings/`: the
  upstream submission excludes that directory, so the docstring in
  `step_order.py` is the model.

## 6. Decisions

Decided 2026-10-10: the managed budget (section 3f) replaces the
ceilings that only moved down. Still open:

1. **Venv patching by the shim** (wave 1, item 7): apply known-defect
   patches automatically, or keep them as a documented script the agent
   runs. The findings show both reboot-crm and new-crm doing it by hand
   and losing the patch on every `uv sync`.
2. **`resolved_by` beyond `skills/`** (section 3b): a schema change the
   Plugin Browser reads; its "Covered in" label would gain a mechanism.
3. **Where the API lint runs**: inside the `rbt` shim on every
   `generate` (catches it in the agent's loop) or only in `prove.yml`
   (catches it at the pull request).
