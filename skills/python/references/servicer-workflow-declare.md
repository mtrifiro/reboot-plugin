---
title: Declaring and Starting a Workflow
impact: CRITICAL
impactDescription: A workflow written as an instance method, declared as a factory, or started with schedule() from another workflow fails at codegen or retries forever
tags: workflow, WorkflowContext, classmethod, Workflow, schedule, spawn, factory, start, claim
summary: "A workflow is a `@classmethod` taking `WorkflowContext`, never an instance method or a factory; start it with `schedule()`, but from another workflow with `spawn()`."
step: servicer
applies: [mcp-ui, web-app, backend-only]
always: false
when: "you declared a `Workflow`"
via: servicer-workflow.md
verified: 1.6.0
docs: ""
---

# Declaring and Starting a Workflow

## When you are here

You are writing a `Workflow(...)` servicer or starting one. It is
checkpointed at every memoized step and `context.loop` iteration, so it
resumes after a restart and can run for days. Body contents: the other
parts in [`servicer-workflow.md`](servicer-workflow.md).

## Do this

API: `run_hello=Workflow(request=RunHelloRequest, response=None, description="…", mcp=None)`.
Servicer: a **`@classmethod`** taking `WorkflowContext`, with no `self`
or `self.state`, because the body re-executes on replay and instance
attributes do not survive it. To start it on actor creation, make the
constructor a `Writer(factory=True)` or `Transaction(factory=True)` that
schedules it last; `schedule()` with no `when=` fires on commit.

```python
from greeter.v1.greeter_rbt import Greeter
from reboot.aio.contexts import TransactionContext, WorkflowContext


class GreeterServicer(Greeter.Servicer):

    async def hello(
        self,
        context: TransactionContext,
        request: Greeter.HelloRequest,
    ) -> None:
        # `hello` is `Transaction(factory=True)`; runs after commit.
        await self.ref().schedule().run_hello(context, name=request.name)

    @classmethod
    async def run_hello(
        cls,
        context: WorkflowContext,
        request: Greeter.RunHelloRequest,
    ) -> None:
        # Durable body; read with Greeter.ref().read(context).
        async def set_greeting(state):
            state.greeting = f"hello, {request.name}"
        await Greeter.ref().write(context, set_greeting)
```

- Mutate with `Greeter.ref().<scope>.write(context, fn)`
  ([`servicer-workflow-calls.md`](servicer-workflow-calls.md)); actor
  id is `context.state_id`.
- `response=None` is common (effects are observed through state):
  return `-> None` with no `return` (rule in `api-methods.md`).

`await Greeter.Hello(ctx, "alice", name="alice")` creates the actor and
starts `run_hello`. Start form by caller (1.6.0 generated client):

| Caller | Form | Reaches |
| --- | --- | --- |
| Writer | `self.ref().schedule(when=…).wf(context, …)` | own actor only |
| Transaction | `Type.ref(id).schedule(when=…).wf(context, …)` | any actor |
| Workflow | `Type.ref(id).spawn(when=…).wf(context, …)`, or `.per_workflow("alias").spawn(…)` | any actor |
| Workflow | `await Type.ref(id).wf(context, …)` | spawns it and waits for its response |
| `ExternalContext` / `initialize` | `Type.ref(id).spawn(…)`; in `initialize`, `.idempotently("alias").spawn(…)` | any actor |
| Reader | cannot start a workflow | — |

A bare `spawn()` in a workflow is scoped `per_workflow` (`per_iteration`
inside `context.loop`); name the alias when one workflow spawns more
than once.

## Never

- `cls.ref()` or `self.ref()` inside the workflow — `cls.ref` is an
  instance method of the generated `BaseServicer`. Use `MyType.ref()`
  from `<name>_rbt` (no argument = `context.state_id`).
- `async def wf(self, context: WriterContext, …)` — use `@classmethod`,
  `cls`, `WorkflowContext`.
- `self.state.x = …` in a workflow — use an inline `write`
  ([`servicer-workflow-calls.md`](servicer-workflow-calls.md)).
- `Workflow(factory=True)` — type-checks (`factory: bool` is on the base
  model) but `rbt generate` rejects it. Use a factory writer/transaction
  that schedules the workflow.
- `Type.ref(id).per_workflow("…").schedule(when=…).wf(context)` from a
  workflow — `schedule()` takes only `TransactionContext` (another
  actor) or `WriterContext | TransactionContext` (own actor); it raises
  and retries forever, unseen by mypy. Use `spawn(when=…)`.
- `asyncio.create_task(...)` / `asyncio.sleep` to start or defer work —
  not durable. Use `schedule` / `spawn`.
- Starting the same workflow from two places with nothing stopping
  overlap (a startup hook plus an admin button) — each start runs
  concurrently (16 concurrent passes observed at 1.6.0). Write the
  pass's start time as a claim in the atomic check-and-set that marks it
  running; a pass finding a live claim returns without a successor.

## Limits

- Constructors cannot be scheduled or spawned; only non-constructor
  methods appear on `schedule()` / `spawn()`.
- A claim needs one staleness window, not separate "too old to work" and
  "too young to ignore" limits, or the holder can be too old to run
  while nobody may take over. A pass standing down for age releases its
  claim (observed at 1.6.0).
- Stopping `rbt dev run` pauses a workflow; the next start replays and
  continues it. To stop recurring work, check an app-level flag, or
  expunge.

## Scales as

- "Do this to N things" in one transaction makes all N actors
  two-phase-commit participants; fan out from a workflow with one small
  call each. 216 seat creations: 54 s as a transaction chain, 15.7 s as
  a workflow (measured at 1.4.0). Scheduling onto N actors from a
  transaction crashed the dev database worker under contention
  ([`scheduling-basic.md`](scheduling-basic.md)).

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `Message type "rbt.v1alpha1.WorkflowMethodOptions" has no field named "constructor"` | `factory=True` on a `Workflow` | Factory writer/transaction schedules it |
| `TypeError: reboot.aio.contexts.WorkflowContext is not an instance or subclass of one of the expected type(s): ['reboot.aio.contexts.TransactionContext']` | `schedule()` called from a workflow | `spawn(when=…)` |
| `TypeError: <YourType>BaseServicer.ref() missing 1 required positional argument: 'self'` | `cls.ref()` in a workflow | `MyType.ref()` |
| `is a workflow and must be scheduled from a 'WriterContext' via` | Writer/transaction called a workflow directly | `self.ref().schedule().wf(context, …)` |
| `` `ref()` called without a `state_id` can only be used within a Workflow. `` | `Type.ref()` with no id outside a workflow | `self.ref()` or `Type.ref(id)` |

## See also

- [`servicer-workflow-calls.md`](servicer-workflow-calls.md) — classify every awaited call
- [`scheduling-basic.md`](scheduling-basic.md) — which context schedules what
- [`api-methods.md`](api-methods.md) — the exact servicer signature
