---
title: Implement Writer Methods
impact: HIGH
impactDescription: Writer methods are the only path to mutate single-actor state; a writer that reaches another actor's writer raises, and an external call in one fires twice or survives a rollback
tags: servicer, writer, WriterContext, state, mutation, effect validation, schedule
summary: "A writer mutates `self.state` on one actor only: no writes to other actors, no external calls, schedule only on itself; errors roll back the mutation; writers may return no response."
step: servicer
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: "https://docs.reboot.dev/develop/side_effects"
---

# Implement Writer Methods

## When you are here

You are implementing a method declared `Writer(...)` in the API file:
it receives a `WriterContext` and is the place to mutate `self.state`
for **one** actor. Writers on one actor are serialized; writers on
different actors run independently. Cross-actor mutation is
`servicer-transaction.md`; the exact signature codegen requires is in
`api-methods.md`. The public docs allow an idempotent side effect in
any method run as a task; this skill deliberately tightens that: an
external call goes in a `Workflow`, never in a writer.

## Do this

Matches the [`reboot-bank-pydantic`](https://github.com/reboot-dev/reboot-bank-pydantic) example's `AccountServicer`:

```python
from bank.v1.account_rbt import Account
from reboot.aio.contexts import WriterContext


class AccountServicer(Account.Servicer):

    async def deposit(
        self,
        context: WriterContext,
        request: Account.DepositRequest,
    ) -> None:
        self.state.balance += request.amount
```

`self.state` is the typed state `Model`; assignments and collection
mutations (`self.state.messages.append(request.message)`) persist when
the writer commits.

**What a writer may do:** read and mutate its own state; call
**readers** on other actors; schedule work on **itself** with
`self.ref().schedule(...)` (`scheduling-basic.md`), including
scheduling a `Workflow` that makes an external call.

**Raise a declared error to undo.** Raising `<Method>Aborted` after
mutating `self.state` rolls the mutation back:

```python
async def withdraw(
    self, context: WriterContext, request: Account.WithdrawRequest,
) -> None:
    self.state.balance -= request.amount
    if self.state.balance < 0:
        # The decrement above rolls back automatically.
        raise Account.WithdrawAborted(
            OverdraftError(amount=-self.state.balance)
        )
```

**`response=None`** is valid: the method returns `-> None` and has no
`return` value (`api-methods.md`).

## Never

- Calling another actor's writer, transaction or constructor:

  ```python
  self.state.balance += request.amount
  await Account.ref("audit-log").record(context, ...)  # WRONG
  ```

  It raises `TypeError` (see Errors); a writer cannot call any writer
  through a ref, not even its own via `self.ref()` (observed at
  1.6.0). Cross-actor mutation is a `Transaction`.
- `Other.ref(id).schedule(...)` from a writer — scheduling on another
  actor takes a `TransactionContext` only; mypy reports an overload
  mismatch (reboot-air-150-10, theater-network-19). Schedule a method
  on `self` that reaches the other actor; make it a `Workflow` if it
  should not hold this actor's lock while it runs. Each type that needs
  this grows the same small hand-off workflow (reboot-crm-93, 1.6.0).
- An external call (SMS, email, payment, LLM, network, filesystem) in
  a writer, **even an idempotent one**. A writer can run inside a
  transaction that later aborts, rolling state back after the call
  already happened, and its body re-runs on retries and under effect
  validation, firing the call twice (a real bug: an SMS login code sent
  twice, the first invalidated). Put the call in a `Workflow` and have
  the writer `schedule()` it; the primitive is chosen in
  `servicer-workflow-external.md`.
- Persisting a fresh `uuid4()` or clock value that something later
  re-derives or addresses (an actor id, an idempotency key). A value
  that is only displayed is fine. See `patterns-time-and-randomness.md`.

## Limits

- The runtime may re-execute a writer's body: on transient retries,
  and in development as **effect validation**, which aborts the first
  run of the body, discards its effects, and runs it again; only the
  second run commits, and the two runs are never compared (1.6.0
  source). So the body must be safe to run more than once: confine it
  to `self.state` mutations and in-system calls. A clock or random
  value differs between the runs and the second one is kept; that is
  harmless when the value is only observed (cineloop-06,
  reboot-air-150-05, student-system-08).
- No `context.now()` or RNG exists on `WriterContext` (1.6.0).
- A writer's scope is one actor: its own state, plus reads elsewhere.

## Scales as

- Writers on one actor are serialized, so one actor's write throughput
  bounds every flow that writes it; measured costs are in
  `patterns-load-and-benchmarking.md`.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `TypeError: reboot.aio.contexts.WriterContext is not an instance or subclass of one of the expected type(s)` | The writer called a writer, transaction or constructor through a ref | Make the method a `Transaction`, or schedule the work |
| `No overload variant matches argument types "WriterContext"` | mypy's form of the same, also for `schedule()` on another actor | Same |
| `Re-running method` | Info: effect validation re-runs the body; the second run commits | None needed |

## See also

- [`servicer-transaction.md`](servicer-transaction.md) — when a writer can't
- [`servicer-workflow-external.md`](servicer-workflow-external.md) — where external calls go
- [`patterns-time-and-randomness.md`](patterns-time-and-randomness.md) — clock and ids in bodies
