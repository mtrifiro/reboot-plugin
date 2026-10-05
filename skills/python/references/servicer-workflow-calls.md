---
title: Classifying Workflow Calls and Calling Reboot
impact: CRITICAL
impactDescription: The wrong primitive on an await double-charges users, poisons a workflow forever, or re-runs a write on every replay
tags: workflow, classify, per_workflow, per_iteration, always, idempotently, alias, inline write, scope, replay
summary: "Classify every awaited call first; Reboot calls take `.per_workflow(alias)`, `.per_iteration(alias)` or `.always()`, stable aliases; inline writes."
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

You are about to `await` in a workflow body. Anything may re-run on
replay, so every `await` needs the primitive that makes a rerun safe.
External calls:
[`servicer-workflow-external.md`](servicer-workflow-external.md);
waiting: [`servicer-workflow-wait.md`](servicer-workflow-wait.md).

## Do this

### Classify before you write the call

| Call | Primitive |
| --- | --- |
| `SomeType.ref(id).method(context, …)` — any method on any actor | `.per_workflow(alias)` / `.per_iteration(alias)` / `.always()` |
| `Service.ref().write(context, fn)` — inline mutation of this actor | same scope chain |
| `agent.run(context, prompt)` — Reboot `Agent` (LLM) | none; it memoizes the model call ([`agent-pydantic-ai.md`](agent-pydantic-ai.md)) |
| HTTP, Stripe, Twilio, S3, the clock, randomness — external | `at_least_once` (default) or `at_most_once` |
| Block until Reboot state satisfies a condition | `until` / `until_changes` |

Delayed/background work on an actor is Reboot too, but from a workflow
it is `spawn(when=…)`, never `schedule(when=…)`
([`servicer-workflow-declare.md`](servicer-workflow-declare.md)).

### Aliases: stable and descriptive

Every alias (scope chain, `at_least_once`, `at_most_once`, `until`,
`until_changes`) is the memo key and the step's title in logs:

- **Stable**: never from the clock, fresh UUIDs or randomness; never
  renamed after a run. Loop `iteration` (`f"Process batch {iteration}"`)
  and request ids (`f"Reset {showing_id}"`) are fine.
- **Descriptive**: verb + object (`"Charge customer"`,
  `"Send login SMS"`, not `"Charge"`).

### Reboot calls: pick a scope

Reboot calls are already durable; choose only how often one runs
across replays:

- **`.per_workflow(alias)`** — once per workflow lifetime; replays return
  the memo. Setup, recording a decision, starting a child workflow.
- **`.per_iteration(alias)`** — once per `context.loop` iteration.
- **`.always()`** — never memoized; a live read on every wake.

```python
from uuid import uuid4
from reboot.aio.contexts import WorkflowContext


@classmethod
async def control_loop(
    cls, context: WorkflowContext, request: ControlLoopRequest,
) -> None:
    await Notifier.ref(request.user_id).per_workflow(
        "Welcome notification",
    ).notify_signup(context, name=request.name)

    # Inline write to this actor: `async def`, parameter named `state`.
    async def add_post_for_approval(state):
        state.posts_for_approval.append(
            Post(id=str(uuid4()), author=request.name, text=request.text),
        )

    await Chatbot.ref().per_workflow(
        "Add post for approval",
    ).write(context, add_post_for_approval)

    async for iteration in context.loop("Process"):
        batch = await Queue.ref(queue_id).per_iteration(
            "Dequeue batch",
        ).dequeue(context, bulk=True)
        config = await ConfigService.ref().always().read(context)
```

- Default scope when omitted: `PER_WORKFLOW` outside a loop,
  `PER_ITERATION` inside (`always()` inside an `until` callable); same
  for `at_least_once`, `at_most_once`, `until`; `until_changes` is
  loop-only. The enum form (`("alias", PER_WORKFLOW)`, from
  `reboot.aio.workflows`) is equivalent; prefer the chain.
- `.idempotently("alias")` is the older sibling of `.per_workflow("alias")`
  (same default, not deprecated). In a workflow use the chain; outside
  workflows (`initialize`) `.idempotently` is right, because
  `.per_iteration` is rejected there
  ([`lifecycle-initialize-hook.md`](lifecycle-initialize-hook.md)).

### This actor's state

- The write callback is called as `writer(state=typed_state)`: mutate
  `state`; it commits with the checkpoint. `.write(...)` returns the
  callback's return value, the basis of atomic check-and-update
  ([`servicer-workflow-wait.md`](servicer-workflow-wait.md)).
- Reads use the same chain: `await Chatbot.ref().read(context)`
  (default scope), `Chatbot.ref().always().read(context)` (live).
- Inline `.read()` / `.write()` exist only on the no-arg `ref()`. For
  **another** actor call its declared `Writer`/`Transaction` (scoped) or
  `Reader`.
- To create actors / mutate several states atomically, call one
  `Transaction` on the workflow's own actor:
  `Thread.ref(context.state_id).per_workflow("Finalize").finalize_response(context, …)`.
  A replay returns the cached result, not duplicates (observed working
  at 1.4.1; the authorizer must admit app-internal calls).

## Never

- `at_least_once(...)` / `at_most_once(...)` / `.idempotently(...)`
  around a Reboot call — redundant; `at_most_once` adds a
  poison-the-alias failure mode.
- `async def make_move(s):` — the parameter must be named `state`.
- `def try_claim(state) -> bool:` passed to `.write` — it is awaited;
  use `async def`.
- `Other.ref(id).read(context)` / `.write(context, fn)` — no inline
  read/write on a ref with an id; use declared methods.
- `asyncio.gather` over **transaction** calls in one workflow — siblings
  contend through the shared workflow root and all die at their lock
  deadline (8 concurrent, observed at 1.4.0). Run transactions
  sequentially; gathering **writer** calls is fine.
- Calling the same method on the same actor twice with a bare
  `.per_workflow()` / `.per_iteration()` — the auto key collides; give
  each its own alias.
- Calling a factory constructor from a workflow on an actor that may
  already exist — aborts `StateAlreadyConstructed` and retries forever
  (observed at 1.6.0). Construct once, then call a writer.

## Limits

- A memoized call returns its **first** run's response on every replay;
  "what happened" fields (counts, `created` flags) describe that run.
- Reusing an alias with a different request is refused (see Errors):
  requests under one alias must be replay-stable too.
- Scoped call results type as `Any`; mypy misses wrong field names
  (observed at 1.4.0).

## Scales as

- Gathered writer calls from one workflow: ~20 concurrent was the sweet
  spot; ~54 concurrent made calls ping out and retry-loop (103 s vs.
  15.7 s for the same 216 creations, measured at 1.4.0).

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `got an unexpected keyword argument 'state'` | Inline writer callback parameter not named `state` | Rename it: `async def fn(state)` |
| `TypeError: object str can't be used in 'await' expression` | Inline writer callback is a plain `def` | `async def` |
| `more than once using the same context an idempotency alias or key must be specified` | Same method on the same actor called twice without distinct aliases | Give each call an alias |
| `is being reused _unsafely_; you can not reuse an idempotency key with a different request` | One alias, different request on replay | Make the request replay-stable, or use a new alias |
| `` `read()` is currently only supported within workflows `` | Inline `read()` on a ref with an id | Call a declared `Reader` |

## See also

- [`servicer-workflow-external.md`](servicer-workflow-external.md) — non-Reboot calls and the clock
- [`servicer-workflow-loop.md`](servicer-workflow-loop.md) — what `per_iteration` iterates over
- [`rpc-refs.md`](rpc-refs.md) — constructing refs and ids
