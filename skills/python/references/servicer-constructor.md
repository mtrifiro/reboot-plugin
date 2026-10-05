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

Implementing a method declared `factory=True` on its `Writer(...)` or
`Transaction(...)`: the actor's explicit creation path. Calling it
(`Service.<ctor>(context, id)`, the `(ref, response)` tuple):
`rpc-constructor-calls.md`; exact signature: `api-methods.md`.

## Do this

```python
# api/bank/v1/account.py: open=Writer(request=OpenRequest, response=None, factory=True, ...)
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

- The body runs only when the actor does not exist; on an existing one
  the runtime aborts with `StateAlreadyConstructed` first, so inside an
  explicit constructor `context.constructor` is always `True` and needs
  no branch (1.6.0 source, `state_managers.py`; observed at 1.6.0).
- In a type with a factory, non-constructor methods see
  `context.constructor == False` (observed at 1.6.0).
- In a type with **no** factory, the first writer or transaction call
  constructs the actor implicitly and sees `context.constructor ==
  True` for that call only; gate first-write initialization there:

```python
async def send(
    self, context: WriterContext, request: ChatRoom.SendRequest,
) -> None:
    if context.constructor:
        self.state.topic = "general"
    self.state.messages.append(request.message)
```

- Create and use a new actor atomically from a transaction:

```python
account, _ = await Account.open(context, request.account_id)  # TransactionContext
await account.deposit(context, amount=request.initial_deposit)
```

- Create singletons in the `initialize` hook
  (`await Bank.create(context, SINGLETON_BANK_ID)`, `create` being
  `Bank`'s factory); why that is safe every boot:
  `lifecycle-initialize-hook.md`.

## Never

- **Initial state in `__init__`** (`self.state.balance = 0  # WRONG`).
  Servicer instances are created lazily and reused; set state in the
  constructor method.
- **A "create or re-open" constructor.** On an existing actor it aborts
  `StateAlreadyConstructed`; branching on `context.constructor` changes
  nothing; a retrying workflow loops forever (reboot-crm-68, 1.6.0).
  For get-or-create, probe with a reader first (`rpc-refs.md`) or catch
  `StateAlreadyConstructed` and fall through to an ordinary writer.
  Only a reused idempotency key (`initialize`'s automatic key, a
  repeated `.idempotently(alias)`) returns the stored result instead.
- **Stamping `context.auth` in a constructor reached from another
  servicer.** A nested `create` is app-internal with `context.auth`
  `None`, so an "owner" or first history entry comes out empty
  (reboot-crm-03, 1.6.0). Pass it as a request field
  (`servicer-authorizer.md` § Never).
- **A `Writer(factory=True)` that may one day construct another actor
  or write a second state.** A writer cannot call another actor's
  writer or constructor (`TypeError`, see Errors), and an existing
  `Writer` constructor cannot become a `Transaction` on persisted state
  (reboot-crm-12, 1.6.0). If in doubt, declare
  `Transaction(mode=Exclusive(), factory=True)` from the start.
- **A field added to the constructor later, expected on existing
  actors.** Their constructor never reruns, so it stays at its zero
  value; allocate lazily (`rpc-refs.md` § Never).
- **Re-deriving a `uuid4()` id minted in the constructor.** Reading it
  back from state is fine (`patterns-time-and-randomness.md`).

## Limits

- Callable only from a `TransactionContext`, `WorkflowContext` or
  `ExternalContext` (which includes `InitializeContext`), never a
  reader or writer (generated signature, 1.6.0).
- Constructors cannot be scheduled and are not on `Service.ref(id)` or
  `Service.forall(ids)` (1.6.0 template).
- Changing a constructor between `Writer` and `Transaction` on
  persisted state is refused at boot, even with `factory=True`
  unchanged (reboot-crm-12, 1.6.0); `api-schema-evolution.md` lists the
  kind change as compatible without this exception.
- In development, effect validation runs the body twice; the first
  run's effects, including actors a transaction constructor created,
  are discarded (1.6.0 source).
- `Transaction -> Writer factory` nesting is proven. Deeper chains
  (transaction factories calling transaction factories that construct
  stdlib actors) were part of a hang at 1.4.0, not retested at 1.6.0
  (theater-network-05); keep creation shallow.

## Scales as

- Not measured.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `aborted with 'StateAlreadyConstructed'` | Constructor called on an existing actor (e.g. `OpenAborted: aborted with 'StateAlreadyConstructed'`) | Probe first, or catch it and call an ordinary writer |
| `Reboot options for method` `...` `updated from` | A persisted constructor's kind changed between `Writer` and `Transaction` | Revert the kind; construct the other actor elsewhere |
| `TypeError: reboot.aio.contexts.WriterContext is not an instance or subclass of one of the expected type(s)` | A writer (constructor or not) called another actor's writer or constructor | Make the method a `Transaction` |

## See also

- [`rpc-constructor-calls.md`](rpc-constructor-calls.md) — how callers invoke a constructor
- [`lifecycle-initialize-hook.md`](lifecycle-initialize-hook.md) — singletons and replayed creates
- [`api-methods.md`](api-methods.md) — the exact factory method signature
