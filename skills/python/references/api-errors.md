---
title: Define and Raise Typed Errors
impact: HIGH
impactDescription: Untyped failures become opaque RPC errors at the call site
tags: errors, MethodAborted, errors-list, typed-failures, raise, rollback
summary: "Declare error Models in `errors=[...]` and raise the generated `<Method>Aborted(...)`, never an untyped exception; raising rolls back the mutation."
step: api
applies: [mcp-ui, web-app, backend-only]
always: false
when: "the API declares typed errors"
verified: 1.6.0
docs: ""
---

# Define and Raise Typed Errors

## When you are here

A method can fail in a way its caller must act on (overdraft, seat
taken, limit reached), and you are declaring that failure in the API
and raising it from the servicer. This file owns declaring and
**raising**. Catching, inspecting `.error`, and carrying an error
across an actor boundary are in
[`patterns-error-handling.md`](patterns-error-handling.md).

## Do this

An error is an ordinary `Model`, listed in the method's `errors=[...]`.
`rbt generate` emits one exception class per method,
`<Type>.<Method>Aborted`, named after the **method**, not the error.
Raise it with an error instance. From the
[`reboot-bank-pydantic`](https://github.com/reboot-dev/reboot-bank-pydantic)
example, `api/bank/v1/account.py`:

```python
from reboot.api import API, Field, Methods, Model, Type, Writer


class OverdraftError(Model):
    amount: float = Field(
        tag=1,
        default=0.0,
        description="By how much the withdrawal exceeded the balance, in "
        "dollars.",
    )


class WithdrawRequest(Model):
    amount: float = Field(tag=1, default=0.0)


AccountMethods = Methods(
    withdraw=Writer(
        request=WithdrawRequest,
        response=None,
        errors=[OverdraftError],
        description="Take funds out, or raise `OverdraftError` if the "
        "balance would go negative.",
        mcp=None,
    ),
    # ... other methods ...
)
```

`backend/src/account_servicer.py`:

```python
from bank.v1.account import OverdraftError
from bank.v1.account_rbt import Account
from reboot.aio.contexts import WriterContext


class AccountServicer(Account.Servicer):

    async def withdraw(
        self,
        context: WriterContext,
        request: Account.WithdrawRequest,
    ) -> None:
        self.state.balance -= request.amount
        if self.state.balance < 0:
            raise Account.WithdrawAborted(
                OverdraftError(amount=-self.state.balance)
            )
```

Raising a `<Method>Aborted` inside a `Writer` or `Transaction` rolls
back every state change that method made, so the servicer above may
mutate first and check after: no compensating undo. Give the error
fields the payload the caller needs to say something specific (which
seat, how far over the limit), and name the error and its condition in
the method's `description=`.

## Never

- `raise ValueError("not enough funds")` (or any non-`Aborted`
  exception) for a business failure — the caller gets
  `<Method>Aborted` carrying `Unknown`, and the message is lost to the
  log. Raise the declared `<Method>Aborted`.
- `return None` (or a sentinel field) to signal failure — ambiguous
  and untyped at the caller. Raise.
- `raise OverdraftError(...)` or `raise Account.OverdraftErrorAborted(...)`
  — a `Model` is not an exception, and the class is named after the
  method: `Account.WithdrawAborted(OverdraftError(...))`.
- Raise an error `Model` the method did not list in its own
  `errors=[...]` — only listed classes are declared; anything else
  fails the type check when the `Aborted` is constructed (1.6.0
  source). Add it to `errors=` (adding is a compatible change; see
  [`api-schema-evolution.md`](api-schema-evolution.md)).
- An error `Model` with no fields — it breaks the generated React
  client at import; see `react-generated-client.md` § Errors you will
  see.

## Limits

- "Declared" means the exact class: the generated `is_declared_error`
  checks `type(error) in <method>.errors` (1.6.0 source), so a
  subclass of a declared error is not declared.
- Rollback covers the raising method's own mutations (and, in a
  transaction, everything the transaction did). It cannot undo an
  external call already made; those belong in a workflow.
- Error fields follow every other `Model`'s field rules
  (`api-pydantic.md`).

## Scales as

- Not measured.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `Unhandled (in '` … `propagating as 'Unknown'` | A method raised a non-`Aborted` exception (or an undeclared one); the caller receives `Unknown` | Declare the error and raise `<Method>Aborted(...)` |

## See also

- [`patterns-error-handling.md`](patterns-error-handling.md) — catching and propagating typed errors
- [`api-methods.md`](api-methods.md) — the `errors=` factory argument
- [`api-pydantic.md`](api-pydantic.md) — field rules for error Models
