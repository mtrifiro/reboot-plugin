---
title: Servicer Patterns — User Front Door, Workflow Magic, Scheduling
impact: CRITICAL
impactDescription: The MCP-UI-specific servicer shape layered on top of `python`'s Servicer rules. The User-side `create_<X>` Transaction is the front door for every application-type instance; a workflow it starts on the new instance must be `.schedule()`-d, not awaited; workflow bodies follow the python workflow references.
tags: servicer, user, transaction, workflow, ref, schedule, spawn, classmethod, inline-writer, front-door
summary: "Never await a workflow from `UserServicer.create_<X>`, `.schedule()` it; the Transaction calls `<X>.create(context)`, returns `state_id`; workflow-body idioms."
step: servicer
applies: [mcp-ui]
always: false
verified: 1.6.0
docs: ""
---

# Servicer Patterns — User Front Door, Workflow Magic, Scheduling

## When you are here

Implementing an MCP UI's servicers ([`api-method-types.md`](api-method-types.md)):
a `UserServicer` whose Transactions create application-type instances,
one servicer per application type, maybe a workflow started on creation.
Base servicer rules (kwargs not Request wrappers, `self.ref().state_id`,
typed `<Method>Aborted`) are in the python skill's `servicer-*.md`,
`rpc-*.md` and `api-errors.md`; workflow bodies start at
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
        # Factory create takes request fields as kwargs, never a Request:
        #   Counter.create(context, title="...", count=0)
        counter, _ = await Counter.create(context)
        return User.CreateCounterResponse(
            counter_id=counter.state_id,
        )


class CounterServicer(Counter.Servicer):

    async def create(self, context) -> None:
        pass  # zero defaults; nothing to do

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

Add every servicer class to `backend/src/servicers/registry.py`, the
one list `main.py` and every test module take.
`<X>.create(context)` with no ID mints one and returns `(ref, response)`;
return `ref.state_id` so the AI can pass it to later tool calls.

### Starting a workflow on the instance you just created

```python
class UserServicer(User.Servicer):

    async def create_game(
        self,
        context: TransactionContext,
        request: User.CreateGameRequest,
    ) -> User.CreateGameResponse:
        game, _ = await Game.create(context, ...)
        # Starts when this transaction commits. Empty request: just `context`.
        await Game.ref(game.state_id).schedule().autoplay(context)
        # Fields as kwargs.
        await Game.ref(game.state_id).schedule().do_ping_periodically(
            context,
            num_pings=10,
            period_seconds=1.0,
        )
        return User.CreateGameResponse(game_id=game.state_id)
```

`.schedule(when=timedelta(...))` delays the start. From the type's own
factory Writer/Transaction: `self.ref().schedule().<workflow>(context)`.
Which context may start a workflow:
[`servicer-workflow-declare.md`](../../python/references/servicer-workflow-declare.md).

### Inside the workflow

The body is a `@classmethod` taking `WorkflowContext`; follow the 1.6.0
python workflow parts, don't improvise:

- Call this actor via the **state class** from `<name>_rbt` with a
  no-argument ref, `MyType.ref()` (ID from `WorkflowContext`; raises
  outside a workflow), under an alias scope:
  `MyType.ref().per_iteration("Send ping").do_ping(context)`
  ([`servicer-workflow-calls.md`](../../python/references/servicer-workflow-calls.md)).
- A mutation only this workflow performs uses an inline writer, an
  `async def` whose parameter is named `state`; declare a Writer only if
  it is also called from outside:

  ```python
  async def increment_count(state):
      state.num_pings += 1

  await MyType.ref().per_workflow(
      "Increment ping count",
  ).write(context, increment_count)
  ```

- Start other work from a workflow with `spawn()`, not `schedule()`
  ([`servicer-workflow-declare.md`](../../python/references/servicer-workflow-declare.md)).
- Loops, external calls (LLMs included), waiting, exiting:
  `servicer-workflow-loop.md`, `-external.md`, `-wait.md`, `-exit.md`.

## Never

- `await Game.ref(game.state_id).autoplay(context)` from a Transaction,
  Writer or Reader — schedule it; only `ExternalContext` and
  `WorkflowContext` may await a workflow.
- `.schedule().autoplay(context, request=Game.AutoplayRequest())` — pass
  fields as kwargs.
- `cls.ref()` or `self.ref()` in a workflow — `cls` is the BaseServicer
  and there is no `self`; use `MyType.ref()`
  ([`servicer-workflow-declare.md`](../../python/references/servicer-workflow-declare.md)).
- Wrapping an inline writer in `at_least_once` / `at_most_once` /
  `.idempotently(...)` — Reboot calls are already durable; scope is the
  only knob.
- A model (LLM) call in the `create_<X>` Transaction — transactions
  retry, so it is billed per retry. Call it from a scheduled workflow
  ([`agent-pydantic-ai.md`](../../python/references/agent-pydantic-ai.md)).

## Limits

- A factory method (`<X>.create`) accepts only `TransactionContext`,
  `WorkflowContext` or `ExternalContext` (1.6.0 generated client) — hence
  the `User` front-door method is a `Transaction`.
- Constructors cannot be scheduled; only non-constructor methods appear
  on `schedule()`.

## Scales as

- Not measured.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `got an unexpected keyword argument 'request'` | `request=` wrapper passed to a scheduled call | Pass fields as kwargs |

## See also

- [`api-method-types.md`](api-method-types.md) — the API these implement
- [`servicer-workflow.md`](../../python/references/servicer-workflow.md) — workflow body, part by part
- [`rpc-constructor-calls.md`](../../python/references/rpc-constructor-calls.md) — constructor call semantics
