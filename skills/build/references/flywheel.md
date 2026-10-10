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
| **Design** | `app` (routing); `feature` 1–2; `build` Design Phase, State Model Assessment, Step 1; `dashboard` (Models, Features); Update Flow 1–4 | Domain model: state types, state IDs, methods, method kinds, who may call. `@wip` feature files | **Accept**: the user accepts the domain model and feature files (`build`, "Accept the design") |
| **Prove** | `build` Steps 2–7; `feature` 2a–5 and fixes; `python`; `run`; `upgrade`; `deploy` checks | Scenario results (`tests/.last-run.json`), mypy, page timing, the model diff | **Merge** (the pull request body) and **Promote** (`scripts/deploy.sh`, its release record) |
| **Observe** | `inspect` (and its "From a finding to a scenario"); `deploy` Step 7; the app's logs | Stored state (`rbt inspect`): the history the design chose to record | A finding becomes a ticket, routed below |

The decisions are the user's. The skills put the evidence in front of
them and wait; they never accept, merge or promote on the user's behalf.
`report` and `FINDINGS.md` sit outside the loop: they are feedback on
Reboot and on these skills, not on the app.

### The routing rule

Every change, whether from a ticket, a failed scenario or a production
finding, goes to one stage. `scripts/model_diff.py` sorts each change
by this rule, measuring from the accepted design (the commit that added
`design/accepted.json`; `<base>` names another revision); use it, don't
judge by eye. A project older than it has no copy: take
`scripts/model_diff.py`, and `tests/last_run.py` with its import in
`tests/conftest.py`, from `build/templates/<front door>/`.

| Change | Goes to |
| --- | --- |
| A state type, field, method, method kind, request or response, or `description=` added, removed or changed under `api/` | **Design**: accept again |
| Who may call a method: a servicer's `authorizer()` added, removed or changed, or a check it calls | **Design** |
| A `Feature:` or `Rule:` added, removed or reworded, or a feature's description | **Design** |
| A scenario removed, or an existing scenario's steps changed | **Design** |
| Other code under `backend/`, `web/` or `frontend/` | **Prove** |
| A new scenario under a `Rule:` that already exists (a fix's reproducing case) | **Prove** |
| `@wip` taken off a scenario, with the user's agreement | **Prove** |

The design names who may call each method (the review table's column),
so an authorizer is design written as code: `model_diff.py` lists every
authorizer change as Design, including one that only carries out the
accepted column; the review says which. A fix that turns out to need a
Design change stops there: show the
model diff, say which rule or declaration changes and why, and take it
through "Accept the design" before writing more code.

### Where the work stands

Asked where things are, answer with the stage and the next decision:
"Prove: 11 of 12 scenarios pass; the merge needs the last one", not a
list of files touched.

### Stage cards

The first time a project reaches one of these moments, say where the
work stands with a short card, in the user's own nouns and two or three
of their own rules; after that, the moment gets one line ("11 of 12
pass; the merge needs the last one"). The stage's name appears once, in
a clause that says what it is for, never as a label; no chapter numbers
or links. The models below are the hotel; write yours.

> **The design, for your review.** Here is the design as I understood
> it: `Room` owns "booked at most once per night", `Reservation.create`
> books every room or none and is called only by the app, and each
> rule has a scenario that will test it. This is the cheapest moment to
> change any of it, before anything depends on it. Take your time; I'll
> wait for your go-ahead or your changes.

> **The prototype is built and tested.** The app is running at
> http://localhost:9991; all 9 scenarios pass. This is the stage where
> the code is checked against the design you accepted, so what you see
> should match the rules we agreed on. Try the screens the way a guest
> or a manager would: anything the prototype shows is missing, like
> what happens when a second guest wants the same night, is a new rule,
> and we can add it to the design from here.

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

The second card follows what was built: the prototype (a first build,
with the URL and the invitation to try it), a feature (above), or a fix
("The fix is in", with the reproducing scenario now passing). The pull
request sentence appears only when the work is on a branch. First time
or not: no `design/` before the first checkpoint, no ledger before the
first deploy.

Tone, for these and any card written later:

- Say what the user gains, not what the agent withholds: "the cheapest
  moment to change it", never "nothing is built until you accept".
- The wait is the agent's choice, not a condition on the user: "I'll
  wait for your go-ahead", never "silence does not count". The rule
  itself is for the agent (Never, below), not for the user to hear.
- The next stage is described when it happens, in the model diff's own
  words, not announced as a gate.
- Their nouns, two or three of their own rules, never the table
  restated.
- One clause of orientation; no stage labels in headers.

## Never

- Writing the implementation (Step 2 onward) before the design is
  accepted, unless the user said up front to build without stopping.
  "No answer is not acceptance."
- Folding a rule change into a "fix": a reworded `Rule:`, a changed
  declaration or a loosened authorizer is a Design change however small
  the diff.
- Calling a deploy, merge or acceptance done for the user: they decide;
  the skills show the evidence.
- Treating a partial test run (`-k`, one module) as evidence for a
  merge or a release: run the full suite.

## Limits

- The model diff reads `api/`, the servicers' `authorizer()` methods
  and `tests/*.feature` statically; a domain model built at import time
  (types generated in a loop), or an authorizer assigned rather than
  defined as a method, is not seen.
- Acceptance is recorded as `design/accepted.json` (the date, a
  fingerprint of `api/` and the feature files) beside `design/review.md`,
  in the commit that holds the accepted design; the user's reasons stay
  in the conversation unless the agent wrote them into `review.md`.
- Observe today is stored state only: no per-request traces.

## Scales as

- Not measured.

## Errors you will see

None known.

## See also

- [`evidence.md`](evidence.md) — the pull request body, the release record
- [`../../feature/SKILL.md`](../../feature/SKILL.md) — rules and scenarios first
- [`../../inspect/SKILL.md`](../../inspect/SKILL.md) — read stored state in Observe
