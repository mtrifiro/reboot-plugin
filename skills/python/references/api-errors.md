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

A caller must act on a failure (overdraft, seat taken, limit
reached). This file owns declaring and **raising**;
catching, `.error`, and crossing actor boundaries are in
[`patterns-error-handling.md`](patterns-error-handling.md).

## Do this

An error is an ordinary `Model` listed in `errors=[...]`. `rbt generate`
emits one exception per method, `<Type>.<Method>Aborted`, named after the
**method**, not the error. From
[`reboot-bank-pydantic`](https://github.com/reboot-dev/reboot-bank-pydantic)
`api/bank/v1/account.py`:

```python
from reboot.api import Field, Methods, Model, Writer


class OverdraftError(Model):
    amount: float = Field(tag=1, default=0.0)  # dollars over the balance


AccountMethods = Methods(
    withdraw=Writer(
        request=WithdrawRequest,
        response=None,
        errors=[OverdraftError],
        description="Take funds out, or raise `OverdraftError` if the "
        "balance would go negative.",
        mcp=None,
    ),
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
        if self.state.balance < 0:  # mutate first, check after: rollback undoes it
            raise Account.WithdrawAborted(
                OverdraftError(amount=-self.state.balance)
            )
```

- Raising `<Method>Aborted` in a `Writer` or `Transaction` rolls back
  every state change the method made; no compensating undo.
- Give error fields the payload the caller needs (which seat, how far
  over), and name the error and its condition in `description=`.

## Never

- `raise ValueError("not enough funds")` (or any non-`Aborted`
  exception) for a business failure — the caller gets `<Method>Aborted`
  carrying `Unknown`; the message only reaches the log.
- `return None` (or a sentinel field) to signal failure — ambiguous and
  untyped. Raise.
- `raise OverdraftError(...)` or `raise Account.OverdraftErrorAborted(...)`
  — a `Model` is not an exception; write
  `Account.WithdrawAborted(OverdraftError(...))`.
- Raise an error `Model` the method did not list in its own
  `errors=[...]` — fails the type check when the `Aborted` is
  constructed (1.6.0 source). Add it to `errors=` (compatible; see
  [`api-schema-evolution.md`](api-schema-evolution.md)).
- An error `Model` with no fields — breaks the generated React client
  at import; see `react-generated-client.md` § Errors you will see.

## Limits

- "Declared" means the exact class: `is_declared_error` checks
  `type(error) in <method>.errors` (1.6.0 source); a subclass is not
  declared.
- Rollback covers the method's own mutations (in a transaction,
  everything it did), not an external call already made; put those in a
  workflow.
- Error fields follow normal `Model` field rules (`api-pydantic.md`).

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
