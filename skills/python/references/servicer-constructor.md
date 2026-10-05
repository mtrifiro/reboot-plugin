---
title: Handle Constructor Methods
impact: HIGH
impactDescription: Initial state set in the wrong place leaks across actors or never runs; a constructor called twice aborts with `StateAlreadyConstructed`
tags: servicer, constructor, context.constructor, create, initialization, factory, StateAlreadyConstructed
summary: "Set initial state in the `factory=True` method, never in `__init__`; a constructor runs once per actor (a second call aborts `StateAlreadyConstructed`); declare `Transaction(factory=True)` if it may construct others."
step: servicer
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: ""
---

# Handle Constructor Methods

## When you are here

You are implementing the body of a method declared with `factory=True`
on its `Writer(...)` or `Transaction(...)`: the actor's explicit
creation path. How callers invoke it (`Service.<ctor>(context, id)`,
the `(ref, response)` tuple) is in `rpc-constructor-calls.md`; the
exact servicer signature codegen requires is in `api-methods.md`.

## Do this

`api/bank/v1/account.py`:

```python
open=Writer(
    request=OpenRequest,
    response=None,
    factory=True,
    description="Bring the account into existence with a zero balance.",
    mcp=None,
),
```

`account_servicer.py`:

```python
from reboot.aio.contexts import WriterContext


class AccountServicer(Account.Servicer):

    async def open(
        self,
        context: WriterContext,
        request: Account.OpenRequest,
    ) -> None:
        self.state.name = request.name
        self.state.balance = 0
```

The body runs only when the actor does not exist yet. On an actor that
exists the runtime aborts with `StateAlreadyConstructed` before the body
is reached, so inside an explicit constructor `context.constructor` is
always `True` and needs no branch (1.6.0 source, `state_managers.py`;
observed at 1.6.0).

**`context.constructor` matters in a type with no factory.** There,
the first writer or transaction call constructs the actor implicitly,
and `context.constructor` is `True` for that one call only. That is the
place to gate first-write initialization:

```python
async def send(
    self, context: WriterContext, request: ChatRoom.SendRequest,
) -> None:
    if context.constructor:
        self.state.topic = "general"
    self.state.messages.append(request.message)
```

In a type that has a factory, a non-constructor method sees
`context.constructor == False` (observed at 1.6.0).

**Creating and using a new actor in one atomic step** is a transaction
calling the constructor:

```python
async def sign_up(
    self, context: TransactionContext, request: Bank.SignUpRequest,
) -> None:
    account, _ = await Account.open(context, request.account_id)
    await account.deposit(context, amount=request.initial_deposit)
```

Singletons are created from the `initialize` hook
(`await Bank.create(context, SINGLETON_BANK_ID)`, where `create` is
`Bank`'s factory method); why that is safe on every boot is in
`lifecycle-initialize-hook.md`.

## Never

- **Initial state in `__init__`.** Servicer instances are created
  lazily and reused; `__init__` is not the creation pass. Set state in
  the constructor method.

  ```python
  class AccountServicer(Account.Servicer):
      def __init__(self):
          self.state.balance = 0  # WRONG
  ```

- **A constructor written as "create or re-open".** Calling it on an
  existing actor aborts with `StateAlreadyConstructed`; branching on
  `context.constructor` inside it changes nothing. From a workflow
  that retries on error, this loops forever (reboot-crm-68, 1.6.0).
  For get-or-create, probe with a reader first (`rpc-refs.md`) or
  catch `StateAlreadyConstructed` and fall through to an ordinary
  writer. Only a call whose idempotency key was already used
  (`initialize`'s automatic key, a repeated `.idempotently(alias)`)
  returns the stored result instead.
- **Stamping `context.auth` in a constructor reached from another
  servicer.** A nested `create` is app-internal: `context.auth` is
  `None` there, so an "owner" or first history entry stamped from it
  comes out empty (reboot-crm-03, 1.6.0). Pass what the caller knows
  as a request field. See `servicer-authorizer.md` § Never.
- **A `Writer(factory=True)` that may one day construct another actor
  or write a second state.** A writer cannot call another actor's
  writer or constructor (it raises `TypeError`, see Errors), and an
  existing `Writer` constructor cannot be changed to a `Transaction`
  against persisted state (reboot-crm-12, 1.6.0). If in doubt, declare
  `Transaction(mode=Exclusive(), factory=True)` from the start.
- **A field added to the constructor later, expected on existing
  actors.** Their constructor never runs again, so the field stays at
  its zero value. Allocate it lazily; see `rpc-refs.md` § Never.
- **An id minted with `uuid4()` in the constructor that something
  later re-derives.** Reading it back from state is fine; re-deriving
  it is not. See `patterns-time-and-randomness.md`.

## Limits

- A constructor is called only from a `TransactionContext`,
  `WorkflowContext` or `ExternalContext` (which includes
  `InitializeContext`), never from a reader or writer (generated
  signature, 1.6.0).
- Constructors cannot be scheduled, and are not on `Service.ref(id)`
  or `Service.forall(ids)` (1.6.0 template).
- Changing a constructor between `Writer` and `Transaction` on
  persisted state is refused at boot, even with `factory=True`
  unchanged (reboot-crm-12, 1.6.0). `api-schema-evolution.md` lists
  the kind change as compatible without this exception.
- In development, effect validation runs the body twice; the first
  run's effects, including actors a transaction constructor created,
  are discarded and only the second run commits (1.6.0 source).
- Nesting: `Transaction -> Writer factory` is proven. Deeper chains
  (transaction factories calling transaction factories that construct
  stdlib actors) were part of a hang at 1.4.0 and were not retested
  at 1.6.0 (theater-network-05). Keep creation shapes shallow.

## Scales as

- Not measured.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `aborted with 'StateAlreadyConstructed'` | The constructor was called on an actor that exists (e.g. `OpenAborted: aborted with 'StateAlreadyConstructed'`) | Probe first, or catch it and call an ordinary writer |
| `Reboot options for method` `...` `updated from` | A persisted constructor's kind changed between `Writer` and `Transaction` | Revert the kind; construct the other actor elsewhere |
| `TypeError: reboot.aio.contexts.WriterContext is not an instance or subclass of one of the expected type(s)` | A writer (constructor or not) called another actor's writer or constructor | Make the method a `Transaction` |

## See also

- [`rpc-constructor-calls.md`](rpc-constructor-calls.md) — how callers invoke a constructor
- [`lifecycle-initialize-hook.md`](lifecycle-initialize-hook.md) — singletons and replayed creates
- [`api-methods.md`](api-methods.md) — the exact factory method signature
