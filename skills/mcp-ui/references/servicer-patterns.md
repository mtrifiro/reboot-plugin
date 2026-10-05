---
title: Servicer Patterns — User Front Door, Workflow Magic, Scheduling
impact: CRITICAL
impactDescription: The MCP-UI-specific servicer shape layered on top of `python`'s Servicer rules. The User-side `create_<X>` Transaction is the front door for every application-type instance; a workflow it starts on the new instance must be `.schedule()`-d, not awaited; workflow bodies follow the python workflow references.
tags: servicer, user, transaction, workflow, ref, schedule, spawn, classmethod, inline-writer, front-door
summary: "`UserServicer.create_<X>` Transaction calls `<X>.create(context)` and returns `state_id`; `.schedule()` a workflow from it, never await; workflow bodies use `MyType.ref()`, `spawn()`, `state`-named inline writers."
step: servicer
applies: [mcp-ui]
always: false
verified: 1.6.0
docs: ""
---

# Servicer Patterns — User Front Door, Workflow Magic, Scheduling

## When you are here

You are implementing the servicers for an MCP UI API
([`api-method-types.md`](api-method-types.md)): a `UserServicer` whose
Transactions create application-type instances, one servicer per
application type, and possibly a workflow started when an instance is
created. The base servicer rules (kwargs not Request wrappers,
`self.ref().state_id`, typed `<Method>Aborted`) are in the python
skill's `servicer-*.md`, `rpc-*.md` and `api-errors.md`. Writing a
workflow body is not covered here: start at
[`servicer-workflow.md`](../../python/references/servicer-workflow.md).

## Do this

### The front door and an application type

```python
from mcp_ui_counter.v1.counter_rbt import Counter, User
from reboot.aio.contexts import (
    ReaderContext,
    TransactionContext,
    WriterContext,
)


class UserServicer(User.Servicer):

    async def create_counter(
        self,
        context: TransactionContext,
    ) -> User.CreateCounterResponse:
        """Create a new Counter and return its ID."""
        # Factory create: pass request fields as keyword args directly
        # — do NOT wrap in a Request object.
        # No-args:    Counter.create(context)
        # With args:  Counter.create(context, title="...", count=0)
        counter, _ = await Counter.create(context)
        return User.CreateCounterResponse(
            counter_id=counter.state_id,
        )


class CounterServicer(Counter.Servicer):

    async def create(self, context) -> None:
        # State is initialized with zero defaults; nothing to do.
        pass

    async def increment(
        self,
        context: WriterContext,
        request: Counter.IncrementRequest,
    ) -> None:
        self.state.value += request.amount

    async def decrement(
        self,
        context: WriterContext,
        request: Counter.DecrementRequest,
    ) -> None:
        self.state.value -= request.amount

    async def get(
        self,
        context: ReaderContext,
    ) -> Counter.GetResponse:
        return Counter.GetResponse(value=self.state.value)
```

One servicer class per type, all registered in `Application(servicers=[...])`.
`<X>.create(context)` with no ID mints a fresh one and returns
`(ref, response)`; return `ref.state_id` so the AI can pass it to later
tool calls.

### Starting a workflow on the instance you just created

```python
class UserServicer(User.Servicer):

    async def create_game(
        self,
        context: TransactionContext,
        request: User.CreateGameRequest,
    ) -> User.CreateGameResponse:
        game, _ = await Game.create(context, ...)
        # Schedule the workflow; it starts when this transaction commits.
        # Empty request: just pass `context`.
        await Game.ref(game.state_id).schedule().autoplay(context)
        # Workflow with fields: pass them as kwargs.
        await Game.ref(game.state_id).schedule().do_ping_periodically(
            context,
            num_pings=10,
            period_seconds=1.0,
        )
        return User.CreateGameResponse(game_id=game.state_id)
```

`.schedule(when=timedelta(...))` delays the start. To start the workflow
from the application type's own factory instead, the factory
Writer/Transaction calls `self.ref().schedule().<workflow>(context)`.
Which context may start a workflow, and how, is the table in
[`servicer-workflow-declare.md`](../../python/references/servicer-workflow-declare.md).

### Inside the workflow

The body is a `@classmethod` taking `WorkflowContext`, and the 1.6.0
shapes are in the python workflow parts — follow them, don't improvise:

- Call back into this actor with the **state class** imported from
  `<name>_rbt` and a no-argument ref: `MyType.ref()` (it reads the ID
  from `WorkflowContext`; outside a workflow it raises). Calls get an
  alias scope: `MyType.ref().per_iteration("Send ping").do_ping(context)`
  ([`servicer-workflow-calls.md`](../../python/references/servicer-workflow-calls.md)).
- A mutation only this workflow performs needs no declared Writer: an
  inline writer, `async def` with its parameter named `state`:

  ```python
  async def increment_count(state):
      state.num_pings += 1

  await MyType.ref().per_workflow(
      "Increment ping count",
  ).write(context, increment_count)
  ```

  Reserve declared Writers for operations also called from outside the
  workflow.
- Start other work from a workflow with `spawn()`, not `schedule()`
  ([`servicer-workflow-declare.md`](../../python/references/servicer-workflow-declare.md)).
- Loops, external calls (LLMs included), waiting and exiting:
  `servicer-workflow-loop.md`, `-external.md`, `-wait.md`, `-exit.md`.

## Never

- `await Game.ref(game.state_id).autoplay(context)` from a Transaction,
  Writer or Reader — a workflow cannot be awaited there. Schedule it as
  above. Only `ExternalContext` and `WorkflowContext` may await one.
- `.schedule().autoplay(context, request=Game.AutoplayRequest())` —
  pass request fields as kwargs, never a `request=` wrapper.
- `cls.ref()` or `self.ref()` in a workflow — `cls` is the
  BaseServicer and there is no `self`; use `MyType.ref()`
  ([`servicer-workflow-declare.md`](../../python/references/servicer-workflow-declare.md)).
- Wrapping an inline writer in `at_least_once` / `at_most_once` /
  `.idempotently(...)` — Reboot calls are already durable; scope is the
  only knob.
- A model (LLM) call in the `create_<X>` Transaction — transactions
  retry, so it is billed per retry. Schedule a workflow and call the
  model there
  ([`agent-pydantic-ai.md`](../../python/references/agent-pydantic-ai.md)).

## Limits

- A factory method (`<X>.create`) accepts only a `TransactionContext`,
  `WorkflowContext` or `ExternalContext` (1.6.0 generated client), which
  is why the `User` front-door method is a `Transaction`.
- Constructors cannot be scheduled; only non-constructor methods appear
  on `schedule()`.

## Scales as

- Not measured.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `is a workflow and must be scheduled from a` | A Transaction/Writer awaited a workflow directly | `Type.ref(id).schedule().wf(context, …)` |
| `got an unexpected keyword argument 'request'` | `request=` wrapper passed to a scheduled call | Pass fields as kwargs |
| `got an unexpected keyword argument 'state'` | Inline writer parameter not named `state` | `async def fn(state)` |

## See also

- [`api-method-types.md`](api-method-types.md) — the API these implement
- [`servicer-workflow.md`](../../python/references/servicer-workflow.md) — workflow body, part by part
- [`rpc-constructor-calls.md`](../../python/references/rpc-constructor-calls.md) — constructor call semantics
