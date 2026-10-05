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

You hold a ref (`Service.ref(id)`, `self.ref()`) and need to call a
method on it from a servicer, `initialize`, a test or an external
client. Getting the ref is in `rpc-refs.md`; constructors in
`rpc-constructor-calls.md`; fan-out over many ids in `rpc-forall.md`.

## Do this

Call `await ref.method(context, **fields)`: the context positional,
the request fields as keyword arguments matching the request `Model`.
It returns the response `Model` (or `None` for `response=None`).

```python
await account.deposit(context, amount=100)   # reboot-bank example

response = await chat_room.messages(context)
print(response.messages)
```

Parallelize independent calls in one transaction with `asyncio.gather`:

```python
import asyncio

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

A writer therefore cannot call any writer through a ref, not even its
own through `self.ref()` (observed at 1.6.0). It mutates `self.state`
directly; anything wider is a `Transaction`. When in doubt, call from
a transaction: it can call any method on any actor.

A helper shared by readers, writers and transactions takes
`reboot.aio.contexts.Context`, the common base of `ReaderContext`,
`WriterContext`, `TransactionContext` and `WorkflowContext`
(`ExternalContext` is not a subclass).

## Never

- `await account.deposit(context, DepositRequest(amount=100))` — use
  kwargs. At 1.6.0 neither mypy nor the runtime rejects a wrapper of
  the method's own request type (`Account.DepositRequest`, which is the
  API module's `DepositRequest`): it runs. But the framework's own
  message calls the form wrong, the examples never use it, and the
  slot is typed `Any` for pydantic APIs, so a wrong object there
  passes mypy (verified at 1.6.0).
- A `dict` or a different model in that slot
  (`deposit(context, {"amount": 1})`) — passes mypy, then raises a bare
  `AssertionError` with no message at call time (observed at 1.6.0).
- `deposit(request)` with the context left out, or a request in the
  options slot — raises `TypeError: Unexpected use of request type`.
- A writer calling another actor's writer (or its own via
  `self.ref()`) — mypy `No overload variant matches argument types
  "WriterContext", ...`; at runtime the `TypeError` in Errors.
- Plain dicts for a kwarg typed `list[Model]` — the runtime coerces
  them, mypy rejects them (`List item 0 has incompatible type
  "dict[str, Any]"; expected "PassengerAssignment"`, reboot-air-150-06,
  1.5.0). Construct the nested `Model` class from the API module
  (`api/<pkg>/v1/<name>.py`); `<Type>.<Model>` exists only for
  request and response types.
- Forwarding `**kwargs: dict[str, str]` into a generated method — mypy
  fails every overload; type the forwarded kwargs as a `TypedDict`
  (student-sor-15, 1.5.0).
- Relying on the caller's identity inside the callee. A call made from
  a servicer is app-internal: `context.auth` is `None` in the callee,
  and anything stamped from it (an audit entry, an owner) is silently
  dropped (reboot-crm-02, 1.6.0). Pass the identity as a request field
  from the method that had the session; the authorizer side is in
  `servicer-authorizer.md` § Never.
- A writer cycle: a transaction on A calls a writer on B while some
  transaction on B calls a writer on A. Two ordinary concurrent
  requests on those paths deadlock, and `rbt generate`, mypy and tests
  all stay silent; the dashboard's call graph draws the cycle without
  flagging it (reboot-crm-25, 1.6.0). It usually means both actors
  hold a copy of one fact: decide which owns it and delete the other.
  A path that returns to A through `per_workflow` (a later transaction
  of its own) is not a cycle, though it greps the same.

## Limits

- Calls are awaited RPCs; a call carries no identity from the caller
  servicer (above).
- Inside a workflow, writer and transaction calls need an idempotency
  choice; see `servicer-workflow-calls.md`.

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
