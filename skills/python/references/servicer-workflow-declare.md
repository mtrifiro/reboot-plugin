---
title: Declaring and Starting a Workflow
impact: CRITICAL
impactDescription: A workflow written as an instance method, declared as a factory, or started with schedule() from another workflow fails at codegen or retries forever
tags: workflow, WorkflowContext, classmethod, Workflow, schedule, spawn, factory, start, claim
step: servicer
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: ""
---

# Declaring and Starting a Workflow

## When you are here

You declared a `Workflow(...)` method in the API and are writing its
servicer method, or you need some other method to kick it off. A
workflow is a long-running, durable function attached to an actor: the
runtime checkpoints it at every memoized step and every `context.loop`
iteration, so after a restart it resumes from the last checkpoint and
can run for seconds or days. What goes *inside* the body is in the
other parts listed in [`servicer-workflow.md`](servicer-workflow.md).

## Do this

API file (`api/chatbot/v1/chatbot.py`):

```python
control_loop=Workflow(
    request=ControlLoopRequest,
    response=None,
    description="Answer messages for as long as the chatbot is "
    "running.",
    mcp=None,
),
```

Servicer: a **`@classmethod`** taking a `WorkflowContext`. There is no
`self` and no `self.state`; the body re-executes on replay and the
runtime cannot carry instance attributes across replays.

```python
from chatbot.v1.chatbot_rbt import Chatbot
from reboot.aio.contexts import WorkflowContext


class ChatbotServicer(Chatbot.Servicer):

    @classmethod
    async def control_loop(
        cls,
        context: WorkflowContext,
        request: Chatbot.ControlLoopRequest,
    ) -> None:
        # Workflow body — durable, restartable, can run for hours.
        ...
```

Read this actor's state with `Chatbot.ref().read(context)` and mutate it
with `Chatbot.ref().<scope>.write(context, fn)`
([`servicer-workflow-calls.md`](servicer-workflow-calls.md)). Use
`context.state_id` for the actor's id. `response=None` is common:
effects are observed through state, so the method returns `-> None`
with no `return` (cross-method rule in `api-pydantic.md`).

### Starting it

To start a workflow when the actor is created, make the constructor a
`Writer(factory=True)` or `Transaction(factory=True)` that schedules the
workflow as its last step. `schedule()` with no `when=` fires as soon
as the surrounding writer/transaction commits.

```python
class GreeterServicer(Greeter.Servicer):

    async def hello(
        self,
        context: TransactionContext,
        request: Greeter.HelloRequest,
    ) -> None:
        # `hello` is `Transaction(factory=True)` — creates the actor.
        # Schedule the workflow to run after this transaction commits.
        await self.ref().schedule().run_hello(context, name=request.name)

    @classmethod
    async def run_hello(
        cls,
        context: WorkflowContext,
        request: Greeter.RunHelloRequest,
    ) -> None:
        async def set_greeting(state):
            state.greeting = f"hello, {request.name}"
        await Greeter.ref().write(context, set_greeting)
```

`await Greeter.Hello(ctx, "alice", name="alice")` both creates the
actor and starts `run_hello`.

Which form starts a workflow depends on the caller's context (verified
in the 1.6.0 generated client):

| Caller | Form | Reaches |
| --- | --- | --- |
| Writer | `self.ref().schedule(when=…).wf(context, …)` | own actor only |
| Transaction | `Type.ref(id).schedule(when=…).wf(context, …)` | any actor |
| Workflow | `Type.ref(id).spawn(when=…).wf(context, …)`, or `.per_workflow("alias").spawn(…)` | any actor |
| Workflow | `await Type.ref(id).wf(context, …)` | spawns it and waits for its response |
| `ExternalContext` / `initialize` | `Type.ref(id).spawn(…)`; in `initialize`, `.idempotently("alias").spawn(…)` | any actor |
| Reader | cannot start a workflow | — |

A bare `spawn()` inside a workflow is scoped `per_workflow` (or
`per_iteration` inside `context.loop`); name the alias when one
workflow spawns more than once.

## Never

- `async def wf(self, context: WriterContext, …)` — an instance method
  with a non-workflow context. Use `@classmethod`, `cls`,
  `WorkflowContext`.
- `self.state.x = …` in a workflow — there is no `self`. Use an inline
  `write` ([`servicer-workflow-calls.md`](servicer-workflow-calls.md)).
- `Workflow(factory=True)` — type-checks (`factory: bool` is on the base
  model) but `rbt generate` rejects it. Use a factory writer or
  transaction that schedules the workflow, as above.
- `Type.ref(id).per_workflow("…").schedule(when=…).wf(context)` from a
  workflow — `schedule()` accepts only a `TransactionContext` (another
  actor) or `WriterContext | TransactionContext` (own actor), so it
  raises on every attempt and the task retries forever. mypy does not
  catch it. From a workflow use `spawn(when=…)`, which takes the same
  `when=`.
- `asyncio.create_task(...)` / `asyncio.sleep` to start or defer work —
  not durable. Use `schedule` / `spawn`.
- Starting the same workflow from two places with nothing stopping
  overlap (a startup hook plus an admin button) — each start is a new
  task, and the passes run concurrently (16 concurrent passes observed
  at 1.6.0). Give the workflow a claim: write the pass's start time in
  the same atomic check-and-set that marks it running, and have a pass
  that finds a live claim return without scheduling a successor.

## Limits

- Constructors cannot be scheduled or spawned; only non-constructor
  methods appear on `schedule()` / `spawn()`.
- A claim needs one staleness window, not two: if "too old to keep
  working" and "claim too young to ignore" are separate limits, the
  holder can be too old to run while nobody may take over. A pass that
  stands down for age releases the claim it holds (observed at 1.6.0).
- Stopping `rbt dev run` pauses a workflow, it does not cancel it: on the
  next start it replays its memoized steps and carries on. To stop
  recurring work, check an application-level flag, or expunge.

## Scales as

- A transaction's cost is its participant set. "Do this to N things" in
  one transaction makes every actor a two-phase-commit participant;
  a workflow that issues one small call per thing does not. 216 seat
  creations: 54 s as a transaction chain, 15.7 s as a workflow (measured
  at 1.4.0). A transaction scheduling onto N actors is an N-party 2PC
  and crashed the dev database worker under contention
  ([`scheduling-basic.md`](scheduling-basic.md)); fan out from a
  workflow instead.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `Message type "rbt.v1alpha1.WorkflowMethodOptions" has no field named "constructor"` | `factory=True` on a `Workflow` | Factory writer/transaction schedules it |
| `TypeError: reboot.aio.contexts.WorkflowContext is not an instance or subclass of one of the expected type(s): ['reboot.aio.contexts.TransactionContext']` | `schedule()` called from a workflow | `spawn(when=…)` |
| `is a workflow and must be scheduled from a 'WriterContext' via` | Writer/transaction called a workflow directly | `self.ref().schedule().wf(context, …)` |
| `` `ref()` called without a `state_id` can only be used within a Workflow. `` | `Type.ref()` with no id outside a workflow | `self.ref()` or `Type.ref(id)` |

## See also

- [`servicer-workflow-calls.md`](servicer-workflow-calls.md) — classify every awaited call
- [`scheduling-basic.md`](scheduling-basic.md) — which context schedules what
- [`api-methods.md`](api-methods.md) — the exact servicer signature
