---
title: Call Actor Methods with Kwargs and a Context
impact: HIGH
impactDescription: A writer called from a WriterContext raises TypeError; a dict or wrong model in the request slot raises a bare AssertionError that mypy does not catch
tags: rpc, call, kwargs, context, await, Context, TypeError, AssertionError, deadlock, TypedDict
summary: "Pass kwargs: `await ref.deposit(context, amount=10)`; writers and transactions can't be called from a WriterContext, even your own; caller identity does not travel; writer cycles deadlock."
step: servicer
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: ""
---

# Call Actor Methods with Kwargs and a Context

## When you are here

You hold a ref (`Service.ref(id)`, `self.ref()`) and call a method from
a servicer, `initialize`, a test or an external client. Refs:
`rpc-refs.md`; constructors: `rpc-constructor-calls.md`; fan-out:
`rpc-forall.md`.

## Do this

`await ref.method(context, **fields)`: context positional, request
fields as kwargs matching the request `Model`; returns the response
`Model` (or `None` for `response=None`).

```python
import asyncio

await account.deposit(context, amount=100)   # reboot-bank example
response = await chat_room.messages(context)  # response.messages

# Independent calls in one transaction run in parallel:
await asyncio.gather(
    from_account.withdraw(context, amount=request.amount),
    to_account.deposit(context, amount=request.amount),
)
```

### Which context may call which method (1.6.0 generated signatures)

| Callee | Callable from |
| --- | --- |
| `Reader` | any: `ReaderContext`, `WriterContext`, `TransactionContext`, `WorkflowContext`, `ExternalContext` |
| `Writer`, `Transaction` | `TransactionContext`, `WorkflowContext`, `ExternalContext` |
| Constructor (`factory=True`) | `TransactionContext`, `WorkflowContext`, `ExternalContext` |
| `Workflow` | scheduled (`.schedule()` / `.spawn()`), not called |

- A writer cannot call any writer through a ref, not even its own via
  `self.ref()` (observed at 1.6.0); it mutates `self.state` directly.
  When in doubt, call from a transaction: it can call any method on any
  actor.
- A helper shared across method kinds takes
  `reboot.aio.contexts.Context`, the base of `ReaderContext`,
  `WriterContext`, `TransactionContext` and `WorkflowContext`
  (`ExternalContext` is not a subclass).

## Never

- `await account.deposit(context, DepositRequest(amount=100))` — use
  kwargs. At 1.6.0 a wrapper of the method's own request type
  (`Account.DepositRequest`, i.e. the API module's `DepositRequest`)
  runs and neither mypy nor the runtime rejects it, but the framework's
  own message calls the form wrong, the examples never use it, and the
  slot is typed `Any` for pydantic APIs, so a wrong object passes mypy
  (verified at 1.6.0).
- A `dict` or different model in that slot
  (`deposit(context, {"amount": 1})`) — passes mypy, then raises a bare
  `AssertionError` with no message (observed at 1.6.0).
- `deposit(request)` without the context, or a request in the options
  slot — `TypeError: Unexpected use of request type`.
- A writer calling another actor's writer (or its own via `self.ref()`)
  — mypy `No overload variant matches argument types "WriterContext",
  ...`; at runtime the `TypeError` in Errors.
- Plain dicts for a `list[Model]` kwarg — the runtime coerces them,
  mypy rejects them (`List item 0 has incompatible type
  "dict[str, Any]"; expected "PassengerAssignment"`, reboot-air-150-06,
  1.5.0). Build the nested `Model` from the API module
  (`api/<pkg>/v1/<name>.py`); `<Type>.<Model>` exists only for request
  and response types.
- Forwarding `**kwargs: dict[str, str]` into a generated method — mypy
  fails every overload; type them as a `TypedDict` (student-sor-15,
  1.5.0).
- Relying on the caller's identity in the callee — a call from a
  servicer is app-internal, `context.auth` is `None`, and anything
  stamped from it (audit entry, owner) is silently dropped
  (reboot-crm-02, 1.6.0). Pass identity as a request field
  (`servicer-authorizer.md` § Never).
- A writer cycle: a transaction on A calls a writer on B while a
  transaction on B calls a writer on A. Two ordinary concurrent
  requests deadlock; `rbt generate`, mypy and tests stay silent and the
  dashboard's call graph draws the cycle without flagging it
  (reboot-crm-25, 1.6.0). Usually both actors hold a copy of one fact:
  pick the owner, delete the other. A return to A through
  `per_workflow` (a later transaction of its own) is not a cycle,
  though it greps the same.

## Limits

- Calls are awaited RPCs carrying no caller identity (above).
- In a workflow, writer and transaction calls need an idempotency
  choice (`servicer-workflow-calls.md`).

## Scales as

- Each call is one RPC through the runtime; costs are in
  `patterns-load-and-benchmarking.md`.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `TypeError: reboot.aio.contexts.WriterContext is not an instance or subclass of one of the expected type(s): ['reboot.aio.contexts.TransactionContext', 'reboot.aio.contexts.WorkflowContext', 'reboot.aio.external.ExternalContext']` | A writer called a writer or transaction (any actor) | Make the caller a `Transaction` |
| `No overload variant matches argument types "WriterContext"` | mypy's form of the same | Same |
| `AssertionError` (empty) | A dict or the wrong model passed where the request goes | Pass kwargs |
| `TypeError: Unexpected use of request type` | A request object passed in the context or options slot | `ref.method(context, field=value)` |
| `is a workflow and must be scheduled from a` | A workflow method called directly | `await ref.schedule().method(context, ...)` |
| `List item 0 has incompatible type "dict[str, Any]"` | mypy: dicts for a `list[Model]` kwarg | Build the API module's `Model` |

## See also

- [`rpc-refs.md`](rpc-refs.md) — getting refs and actor ids
- [`rpc-constructor-calls.md`](rpc-constructor-calls.md) — creating actors, the returned tuple
- [`servicer-authorizer.md`](servicer-authorizer.md) — nested calls carry no identity
