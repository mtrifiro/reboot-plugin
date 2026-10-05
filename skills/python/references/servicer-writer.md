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

Implementing a method declared `Writer(...)`: it takes a
`WriterContext` and mutates `self.state` for **one** actor. Writers on
one actor are serialized; on different actors, independent.
Cross-actor mutation: `servicer-transaction.md`; exact signature:
`api-methods.md`. The public docs allow an idempotent side effect in
any method run as a task; this skill deliberately tightens that: an
external call goes in a `Workflow`, never in a writer.

## Do this

Matches the [`reboot-bank-pydantic`](https://github.com/reboot-dev/reboot-bank-pydantic) example's `AccountServicer`:

```python
from bank.v1.account_rbt import Account
from reboot.aio.contexts import WriterContext


class AccountServicer(Account.Servicer):

    async def withdraw(
        self, context: WriterContext, request: Account.WithdrawRequest,
    ) -> None:  # response=None: no return value (api-methods.md)
        self.state.balance -= request.amount
        if self.state.balance < 0:
            # Raising a declared error rolls back the decrement.
            raise Account.WithdrawAborted(
                OverdraftError(amount=-self.state.balance)
            )
```

- `self.state` is the typed state `Model`; assignments and collection
  mutations (`self.state.messages.append(request.message)`) persist
  when the writer commits.
- A writer may: read and mutate its own state; call **readers** on
  other actors; schedule work on **itself** with
  `self.ref().schedule(...)` (`scheduling-basic.md`), including a
  `Workflow` that makes an external call.

## Never

- Calling another actor's writer, transaction or constructor
  (`await Account.ref("audit-log").record(context, ...)  # WRONG`). It
  raises `TypeError` (see Errors), even for its own writer via
  `self.ref()` (observed at 1.6.0). Use a `Transaction`.
- `Other.ref(id).schedule(...)` — scheduling on another actor takes a
  `TransactionContext` only; mypy reports an overload mismatch
  (reboot-air-150-10, theater-network-19). Schedule a method on `self`
  that reaches the other actor, a `Workflow` if it should not hold this
  actor's lock; each type that needs this grows the same small hand-off
  workflow (reboot-crm-93, 1.6.0).
- An external call (SMS, email, payment, LLM, network, filesystem),
  **even an idempotent one**. An enclosing transaction can abort and
  roll state back after the call happened, and the body re-runs on
  retries and under effect validation, firing it twice (real bug: an
  SMS login code sent twice, the first invalidated). Have the writer
  `schedule()` a `Workflow`; the primitive is chosen in
  `servicer-workflow-external.md`.
- Persisting a fresh `uuid4()` or clock value that is later re-derived
  or addressed (an actor id, an idempotency key); display-only is fine
  (`patterns-time-and-randomness.md`).

## Limits

- The body may re-execute: on transient retries, and in development as
  **effect validation**, which aborts the first run, discards its
  effects and reruns; only the second run commits and the runs are
  never compared (1.6.0 source). Confine the body to `self.state`
  mutations and in-system calls. A clock or random value differs
  between runs and the second is kept, harmless when only observed
  (cineloop-06, reboot-air-150-05, student-system-08).
- No `context.now()` or RNG on `WriterContext` (1.6.0).
- Scope is one actor: its own state, plus reads elsewhere.

## Scales as

- One actor's serialized write throughput bounds every flow that
  writes it; measured costs: `patterns-load-and-benchmarking.md`.

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
