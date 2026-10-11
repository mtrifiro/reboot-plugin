---
title: The Reboot Flywheel
impact: HIGH
impactDescription: Without it the agent builds past an unaccepted design, or sends a design change through as a code fix
tags: flywheel, design, prove, observe, accept, merge, promote, routing, evidence
summary: "Design → Prove → Observe: which skill does what, the decisions, and the rule routing every change."
step: any
applies: [mcp-ui, web-app, backend-only]
always: false
when: "a change might alter the design, or the user asks where the work stands"
verified: 1.6.0
docs: ""
---

# The Reboot Flywheel

## When you are here

Every Reboot app the skills build moves through three stages, in a
loop: **Design** (does the design say what the user means?), **Prove**
(does the code do what the accepted design says?) and **Observe** (what
is the running app doing, and why?). Read this when you need to know
which stage a piece of work is in, which decision ends it, or whether a
change goes back to Design. The evidence each decision rests on is in
[`evidence.md`](evidence.md).

## Do this

### The stages, and what does each

| Stage | Skills and steps | Evidence | Ends with |
| --- | --- | --- | --- |
| **Design** | `app`; `feature` 1–2; `build` Design Phase, State Model Assessment, Step 1; `dashboard` Models and Features; Update Flow 1–4 | The domain model: state types, IDs, methods, kinds, who may call; the `@wip` feature files | **Accept**: the user accepts the model and the feature files on the running first prototype, and each later feature's slice before its implementation (`build`, "Accept the Design") |
| **Prove** | `build` 2–7; `feature` 2a–5 and fixes; `python`; `run`; `upgrade`; `deploy` checks | Scenario results (`tests/.last-run.json`), mypy, page timing, the model diff | **Merge** (the pull request body) and **Promote** (`scripts/deploy.sh` and its release record) |
| **Observe** | `inspect`; `deploy` Step 7; the app's logs | Stored state (`rbt inspect`): the history the design chose to record | A finding becomes a ticket, routed below |

The decisions are the user's: the skills put the evidence in front of
them and wait, never accepting, merging or promoting for them.
`report` and `FINDINGS.md` are feedback on Reboot and on these skills,
outside the loop.

### The routing rule

Every change, from a ticket, a failed scenario or a production finding,
goes to one stage. `scripts/model_diff.py` sorts each by this rule,
measuring from the accepted design (the commit that added
`design/accepted.json`; `<base>` names another revision). Use it, never
judge by eye. A project older than the script takes it, with
`tests/last_run.py` and its `conftest.py` import, from
`build/templates/<front door>/`.

| Change | Goes to |
| --- | --- |
| A state type, field, method, method kind, request or response, or `description=` added, removed or changed under `api/` | **Design**: accept again |
| Who may call a method: a servicer's `authorizer()` added, removed or changed, or a check it calls | **Design** |
| A `Feature:` or `Rule:` added, removed or reworded, or a feature's description | **Design** |
| A scenario removed, or an existing scenario's steps changed | **Design** |
| Other code under `backend/`, `web/` or `frontend/` | **Prove** |
| A new scenario under a `Rule:` that already exists (a fix's reproducing case) | **Prove** |
| `@wip` taken off a scenario, with the user's agreement | **Prove** |

An authorizer is design written as code, so `model_diff.py` lists every
authorizer change as Design, even one that only carries out the
accepted column; the review says which. A fix that needs a Design
change stops: show the model diff, say which rule or declaration
changes and why, and take it through "Accept the Design" before
writing more code.

### Where the work happens

The developer decides whether changes go straight onto `main` or onto
a branch each. The skills follow that choice, never make it.

1. **Follow what the project already does.** The `Workflow:` line in
   `AGENTS.md` once it names a choice; else a branch other than `main`
   already checked out; else what the repository shows
   (`CONTRIBUTING.md`, a rule in `AGENTS.md` or `CLAUDE.md`, merged
   pull requests in `git log`). Say in one line which applies.
2. **Otherwise ask once,** at the first change after the first build,
   which stays on `main`: `Design assumed`, `Prototype`, then
   `Design accepted` once the user accepts:
   > Where should changes go from now on? Straight onto `main`, or a
   > branch for each change that you merge when you're happy with it?
   > With a branch, a pull request on GitHub runs the app's tests and
   > posts what changed before you merge.

   The last sentence only when `origin` is on GitHub.
3. **Record the answer** as the `Workflow:` line in `AGENTS.md`
   (`main`, or `a branch per change, pull requests on GitHub`),
   committed with the change. The developer changes it by saying so.
4. **On a branch,** named for the change or its ticket
   (`add-transfers`, `hotel-7-late-checkout`): say so in one line
   before creating or switching, and never switch over uncommitted
   changes. When the change is proven, the card offers the pull
   request with the [`evidence.md`](evidence.md) body; push and open
   it only on the developer's yes. A deploy ships `main`, so the
   merge, the developer's, comes first.

### Where the work stands

Asked where things are, answer with the stage and the next decision:
"Prove: 11 of 12 scenarios pass; the merge needs the last one", not a
list of files touched.

### The decisions log

`design/decisions.md` keeps why the design is what it is after the
conversation that settled it is gone. Each acceptance appends one
entry, newest last; no entry is edited or removed, so a later change
that overturns one adds its own entry naming it.

```markdown
## 2026-10-10 — Design accepted: Front desk

- **Decided:** each Room is its own state, keyed by hotel and room
  number; `book` is a Writer on Room.
- **Why:** a room is booked at most once per night, and one Room's
  writer is the lock that keeps it so.
- **Set aside:** rooms as a list on Hotel: every booking would lock
  the whole hotel.
- **The user's words:** "housekeeping never sees guest names."
- **Replaces:** nothing (first design).
```

One **Decided** and **Why** pair per choice the user would need
explained later: a state type, a container, a method type, who may
call, the primary view, a deviation from the brief. **Set aside** only
for alternatives raised. **The user's words** quoted, or "accepted
without comment". **Replaces** names the entries overturned, by
heading, or "nothing". A build without stopping gets its entry, headed
"Design not accepted: <title>". Before a change, read the log: a change
against an entry says so to the user first, naming the entry and its
why.

### Stage cards

The first time a project reaches one of these moments, say where the
work stands with a short card, in the user's own nouns and two or three
of their own rules; after that, the moment gets one line ("11 of 12
pass; the merge needs the last one"). The stage's name appears once, in
a clause that says what it is for, never as a label; no chapter numbers
or links. The models below are the hotel; write yours.

> **The first prototype is running, for your review.** The app is up
> at http://localhost:9991; all 12 scenarios pass. It is built on
> the simplest assumptions, so there is something real to review the
> architecture, the rules and the feature set on: `Room` owns "booked
> at most once per night", `Reservation.create` books every room or
> none and is called only by the app, guests sign in with the
> development picker, and the data is disposable. Reboot keeps each
> room as its own actor and runs its methods one at a time, which is
> what makes the first rule hold. Anything the brief left out is a new
> feature, agreed and added one at a time. The look: violet on
> paper, the house default since you named no brand; name one, or a
> site, and it gets read. Try the screens the way a guest would: this
> is the cheapest moment to change any of it. Take your time; the
> build waits for your go-ahead or your changes.

> **The feature is built and tested.** The full suite ran at this
> commit: 11 of 12 scenarios pass; the one that doesn't is "A guest
> cancels the day before check-in". This is the stage where the code is
> checked against the design you accepted. If you open a pull request,
> its description lists the rules the change touched first, so you can
> decide how much code you want to read.

> **Ready to deploy.** The dry run shows what would ship: two commits
> since the last deploy, no change to the design, and a full passing run
> of this exact commit. Deploying is yours to call; say so and it goes.

> **Live.** The app is running in production. If a report comes in,
> `rbt inspect` reads the stored state behind it, and the fix starts
> from a scenario that reproduces it.

The first card is the prototype's review; a later handoff follows what
was built: a feature (above), or a fix
("The fix is in", with the reproducing scenario now passing). The pull
request sentence appears only when the work is on a branch. First time
or not: no `design/` before the first checkpoint, no ledger before the
first deploy.

Tone, for these and any card written later:

- Never the first person: no I, me, my, we or us, in a card or in any
  line to the user. The subject is the app, the design, the build or
  the prototype ("the prototype is running", "the next feature
  follows"), and "you" is the user.
- Verbose and architectural: each step ends in two or three statements
  of fact about the objects, rules and roles it touched and what was
  decided between them; a reference is narrated by what it settled.
  Never an account of what was done or what comes next. The sentence
  rules and the model paragraph are at the head of the build skill
  ("How the build talks").
- Say what the user gains, not what the agent withholds: "the cheapest
  moment to change it", never "nothing is built until you accept". The
  wait is the agent's choice, never a condition on the user.
- The next stage is described when it happens, in the model diff's own
  words, never announced as a gate.
- Their nouns, two or three of their own rules, never the table
  restated. One clause of orientation; no stage labels in headers.

**The ask, in one line.** When a card stops for the user's call (the
design, the deploy), the ask is the card's last line, plain prose in
the user's nouns with the answers it takes: "Accept the design as it
stands, change it (say what), or build on without accepting." No
box, no menu.

## Never

- Asking the brief's open questions before the first prototype runs:
  assume, say so, build, and review on the running app.
- Writing a feature's implementation, after the first prototype, before
  its slice of the design is accepted, unless the user said up front to
  build on. "No answer is not acceptance."
- Creating an object or choosing a method kind without saying so:
  every object and every decision is said as it is made, in the user's
  nouns, with its why.
- Folding a rule change into a "fix": a reworded `Rule:`, a changed
  declaration or a loosened authorizer is a Design change however small
  the diff.
- Calling a deploy, merge or acceptance done for the user: they decide;
  the skills show the evidence.
- Treating a partial test run (`-k`, one module) as evidence for a
  merge or a release: run the full suite.
- Choosing between `main` and branches for the developer, or going
  against the `Workflow:` line in `AGENTS.md`.
- Pushing, or opening, merging or closing a pull request, without the
  developer's yes for that one.

## Limits

- The model diff reads `api/`, the servicers' `authorizer()` methods
  and `tests/*.feature` statically; a domain model built at import time
  (types generated in a loop), or an authorizer assigned rather than
  defined as a method, is not seen.
- Acceptance is recorded as `design/accepted.json` (the date, a
  fingerprint of `api/` and the feature files) beside `design/design.md`
  (the design as accepted), `design/review.md` (its review table) and
  `design/decisions.md` (each acceptance's decisions, reasons and the
  user's words, appended), in the commit that holds the accepted design.
  The reasons are what the agent wrote there: anything said only in
  the conversation is lost with it.
- Observe today is stored state only: no per-request traces.

## Scales as

- Not measured.

## Errors you will see

None known.

## See also

- [`evidence.md`](evidence.md) — the pull request body, the release record
- [`../../feature/SKILL.md`](../../feature/SKILL.md) — rules and scenarios first
- [`../../inspect/SKILL.md`](../../inspect/SKILL.md) — read stored state in Observe
