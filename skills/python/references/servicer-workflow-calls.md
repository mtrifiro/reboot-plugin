---
title: Classifying Workflow Calls and Calling Reboot
impact: CRITICAL
impactDescription: The wrong primitive on an await double-charges users, poisons a workflow forever, or re-runs a write on every replay
tags: workflow, classify, per_workflow, per_iteration, always, idempotently, alias, inline write, scope, replay
summary: "Classify every awaited call before writing it; Reboot calls take `.per_workflow(alias)`, `.per_iteration(alias)` or `.always()` with stable, descriptive aliases; inline writes to this actor's state."
step: servicer
applies: [mcp-ui, web-app, backend-only]
always: false
when: "you declared a `Workflow`"
via: servicer-workflow.md
verified: 1.6.0
docs: ""
---

# Classifying Workflow Calls and Calling Reboot

## When you are here

You are writing the body of a `@classmethod` workflow and are about to
`await` something. Everything a workflow does may be re-run on replay
(after a restart, or after a later step fails), so every `await` needs
the primitive that makes a second run safe. This file classifies the
call and covers Bucket 1, calls into Reboot. External calls are in
[`servicer-workflow-external.md`](servicer-workflow-external.md),
waiting in [`servicer-workflow-wait.md`](servicer-workflow-wait.md).

## Do this

### Classify before you write the call

| What you're calling | Bucket | Primitive |
| --- | --- | --- |
| `SomeType.ref(id).method(context, …)` — reader / writer / transaction / workflow on another (or this) actor | Reboot | `.per_workflow(alias)` / `.per_iteration(alias)` / `.always()` |
| `Service.ref().write(context, fn)` — inline mutation of this workflow's actor | Reboot | same scope chain |
| `agent.run(context, prompt)` — Reboot `Agent` (LLM) | Reboot | none; the `Agent` memoizes the model call ([`agent-pydantic-ai.md`](agent-pydantic-ai.md)) |
| HTTP, Stripe, Twilio, S3, the clock, randomness — anything outside Reboot | External | `at_least_once` (default) or `at_most_once` |
| Block until Reboot state satisfies a condition | Reactive wait | `until` / `until_changes` |

Delayed or background work on an actor is Bucket 1 too, but from a
workflow it is `spawn(when=…)`, never `schedule(when=…)`
([`servicer-workflow-declare.md`](servicer-workflow-declare.md)).

### Name aliases: stable and descriptive

Every alias (scope chain, `at_least_once`, `at_most_once`, `until`,
`until_changes`) is both the memo key and the step's title.

- **Stable.** Identical across replays: never built from wall-clock
  time, fresh UUIDs or randomness, and never renamed once a workflow has
  run. Replay-stable inputs are fine: the `iteration` from
  `context.loop(...)` (`f"Process batch {iteration}"`) or an id from the
  request (`f"Reset {showing_id}"`).
- **Descriptive.** Verb + object — `"Charge customer"`,
  `"Send login SMS"` — not `"Charge"`. It surfaces in logs and tooling.

### Bucket 1: pick a scope

Reboot calls are already durable: a writer/transaction commits or rolls
back atomically and inline writes are checkpointed with the workflow.
The only decision is how often the call runs across replays:

- **`.per_workflow(alias)`** — once for the workflow's lifetime; replays
  return the memoized result. One-shot setup, recording a decision,
  starting a child workflow.
- **`.per_iteration(alias)`** — once per `context.loop` iteration.
- **`.always()`** — never memoized; a live read every time the workflow
  wakes.

```python
from reboot.aio.contexts import WorkflowContext


@classmethod
async def control_loop(
    cls, context: WorkflowContext, request: ControlLoopRequest,
) -> None:
    # One-shot: send the welcome notification once for this workflow.
    await Notifier.ref(request.user_id).per_workflow(
        "Welcome notification",
    ).notify_signup(context, name=request.name)

    # Inline state seed, once per workflow lifetime.
    async def seed(state):
        state.owner = request.name

    await MyType.ref().per_workflow("Seed state").write(context, seed)

    async for iteration in context.loop("Process"):
        # Per-iteration: a fresh scope each tick.
        batch = await Queue.ref(queue_id).per_iteration(
            "Dequeue batch",
        ).dequeue(context, bulk=True)

        # `.always()` — re-read the live config every iteration.
        config = await ConfigService.ref().always().read(context)
```

Omitting the scope picks a default: `PER_WORKFLOW` outside a loop,
`PER_ITERATION` inside one (`always()` inside an `until` callable). The
same applies to `at_least_once`, `at_most_once` and `until`;
`until_changes` is loop-only. The enum form (`("alias", PER_WORKFLOW)`,
from `reboot.aio.workflows`) equals the chain methods; prefer the chain
at call sites.

`.idempotently("alias")` is the older sibling of `.per_workflow("alias")`
(same default, not deprecated). In a workflow body replace it with
`.per_workflow`, `.per_iteration` or `.always()`. Outside workflows
(`initialize`) `.idempotently` is the right tool, because `.per_iteration`
is rejected there ([`lifecycle-initialize-hook.md`](lifecycle-initialize-hook.md)).

### Mutating and reading this actor's state

```python
@classmethod
async def control_loop(
    cls, context: WorkflowContext, request: ControlLoopRequest,
):
    async def add_post_for_approval(state):
        state.posts_for_approval.append(
            Post(id=str(uuid4()), author=request.name, text=text),
        )

    await Chatbot.ref().per_workflow(
        "Add post for approval",
    ).write(context, add_post_for_approval)
```

The callback is an **`async def`** whose parameter is named **`state`**
(the runtime calls `writer(state=typed_state)`). Mutate `state`
directly; the change commits with the workflow checkpoint, and on
replay the scope decides whether the write re-fires or returns its
cached result. The callback may return a value, which `.write(...)`
returns — the basis of atomic check-and-update
([`servicer-workflow-wait.md`](servicer-workflow-wait.md)).

Reads use the same chain: `await Chatbot.ref().read(context)` is the
default-scoped form; `Chatbot.ref().always().read(context)` re-reads
live each iteration.

Inline `.read()` / `.write()` exist only on the no-arg `ref()`. To change
**another** actor, call its declared `Writer`/`Transaction` with a scope;
to observe it, call a declared `Reader`.

To create actors and mutate several states atomically, declare a
`Transaction` on the workflow's own actor and call it once:
`Thread.ref(context.state_id).per_workflow("Finalize").finalize_response(context, …)`.
One memoized Reboot call; a replay returns the cached result instead of
creating duplicates (observed working at 1.4.1; the authorizer must
admit app-internal calls).

## Never

- `at_least_once(...)` / `at_most_once(...)` / `.idempotently(...)`
  around a Reboot call — redundant at best; `at_most_once` adds a
  poison-the-alias failure mode to a call that never needed one.
- `async def make_move(s):` — the parameter must be named `state`.
- `def try_claim(state) -> bool:` passed to `.write` — the callback is
  awaited, so a plain `def` fails. Use `async def`.
- `Other.ref(id).read(context)` / `.write(context, fn)` — no inline
  read/write on a ref with an id. Use the actor's declared methods.
- `asyncio.gather` over **transaction** calls in one workflow — sibling
  transactions contend through the shared workflow root and all die at
  their lock deadline (8 concurrent, observed at 1.4.0). Issue
  transactions sequentially. Gathering **writer** calls is fine.
- Calling the same method on the same actor twice with a bare
  `.per_workflow()` / `.per_iteration()` — the auto-generated key
  collides. Give each call its own alias.
- Calling a factory constructor from a workflow on an actor that may
  already exist — it aborts `StateAlreadyConstructed` and the workflow
  retries forever (observed at 1.6.0). Construct once, then call a writer.

## Limits

- A memoized call returns its **first** execution's response on every
  replay; fields describing "what happened" (counts, `created` flags)
  describe that first run.
- Reusing an alias with a different request is refused (see Errors), so
  request arguments under one alias must be replay-stable too.
- Results of scoped calls type as `Any`; mypy cannot catch a wrong field
  name on them (observed at 1.4.0).

## Scales as

- Gathered writer calls from one workflow: about 20 concurrent was the
  sweet spot; about 54 concurrent made calls ping out and retry-loop
  (103 s vs. 15.7 s for the same 216 creations, measured at 1.4.0).

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `got an unexpected keyword argument 'state'` | Inline writer callback parameter not named `state` | Rename it `state` |
| `TypeError: object str can't be used in 'await' expression` | Inline writer callback is a plain `def` | `async def` |
| `more than once using the same context an idempotency alias or key must be specified` | Same method on the same actor called twice without distinct aliases | Give each call an alias |
| `is being reused _unsafely_; you can not reuse an idempotency key with a different request` | One alias, different request on replay | Make the request replay-stable, or use a new alias |
| `` `read()` is currently only supported within workflows `` | Inline `read()` on a ref with an id | Call a declared `Reader` |
| `StateAlreadyConstructed` | Constructor called on an existing actor | Call an ordinary writer |

## See also

- [`servicer-workflow-external.md`](servicer-workflow-external.md) — non-Reboot calls and the clock
- [`servicer-workflow-loop.md`](servicer-workflow-loop.md) — what `per_iteration` iterates over
- [`rpc-refs.md`](rpc-refs.md) — constructing refs and ids
