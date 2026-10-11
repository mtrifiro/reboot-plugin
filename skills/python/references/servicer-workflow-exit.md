---
title: How a Workflow Exits
impact: HIGH
impactDescription: An undeclared exception retries the workflow forever; a declared abort raised too eagerly fails it on a transient blip
tags: workflow, exit, abort, Aborted, errors, retry, declared error, terminate
summary: "An undeclared exception retries the workflow forever; return, or raise a declared `<Workflow>Aborted` on permanent failures only."
step: servicer
applies: [mcp-ui, web-app, backend-only]
always: false
when: "you declared a `Workflow`"
via: servicer-workflow.md
verified: 1.6.0
docs: ""
---

# How a Workflow Exits

## When you are here

You are deciding what the workflow does on bad input, a declined
payment, or an external failure returned as data (making it data:
[`servicer-workflow-external.md`](servicer-workflow-external.md)).
Stop vs. retry depends on whether the raised exception is declared.

## Do this

A running workflow has three outcomes:

1. **Return normally** — done; any `response=` value is recorded.
2. **Raise a declared `<Type>.<Workflow>Aborted(<Error>(...))`** —
   **terminates**, not retried; the error is its recorded failure,
   inspected like a writer/transaction abort
   ([`api-errors.md`](api-errors.md)).
3. **Raise anything else** (`ValueError`, transient HTTP error, a bug) —
   transient: replayed from the last checkpoint indefinitely, until it
   succeeds, a fix ships, or the state is expunged.

Declare every stopping error in `errors=`:

```python
class PaymentDeclined(Model):
    reason: str = Field(tag=1, default="")


api = API(
    Order=Type(
        state=OrderState,
        methods=Methods(
            fulfill=Workflow(
                request=FulfillRequest,
                response=None,
                errors=[PaymentDeclined, CustomerSuspended],
                description="Take the order from paid to shipped, "
                "resuming where it left off after a restart.",
                mcp=None,
            ),
        ),
    ),
)
```

Raise it **after** the failing step returns its outcome as data:

```python
from reboot.aio.contexts import WorkflowContext
from reboot.aio.workflows import at_most_once
from <pkg>.v1.order_rbt import Order


class OrderServicer(Order.Servicer):

    @classmethod
    async def fulfill(
        cls, context: WorkflowContext, request: Order.FulfillRequest,
    ) -> None:
        async def do_charge() -> ChargeResult:
            try:
                response = await stripe.PaymentIntent.create(
                    amount=request.amount,
                    idempotency_key=f"order:{context.state_id}",
                )
                return ChargeResult(ok=True, charge_id=response.id)
            except stripe.error.CardError as e:
                # Permanent — data, so the alias isn't poisoned.
                return ChargeResult(ok=False, reason=str(e))

        outcome = await at_most_once("Charge", context, do_charge)
        if not outcome.ok:
            # Declared error → workflow stops, not retried.
            raise Order.FulfillAborted(
                PaymentDeclined(reason=outcome.reason),
            )

        async def mark_paid(state):
            state.charge_id = outcome.charge_id
            state.status = "paid"

        await Order.ref().per_workflow(
            "Mark paid",
        ).write(context, mark_paid)
```

After a failure-as-data, choose deliberately:

- **Stop** → raise a declared abort.
- **Continue degraded** → record it with a scoped inline write; proceed.
- **Fallback** → call a different actor or provider.
- **Retry the whole workflow** → let an undeclared exception propagate
  (rare; usually the step's callable raising inside `at_least_once` is
  what you want).

## Never

- `raise ValueError("amount must be positive")` where you mean "stop" —
  bad input stays bad, so it retries forever. Raise
  `Order.FulfillAborted(InvalidRequest(field="amount", reason="must be positive"))`
  with the error declared.
- Catching a transient error and converting it to a declared abort —
  fails the workflow on the first hiccup. Let it propagate.
- `raise` inside an `at_least_once` / `at_most_once` callable to mean
  "stop" — `at_least_once` retries indefinitely; `at_most_once` poisons
  the alias. Return data, decide in the body.
- Raising an abort class whose error is not in the method's `errors=`.

## Limits

- An undeclared exception from a bug retries until a fix ships or state
  is expunged; nothing gives up on its own.
- Stopping the dev server does not end a workflow; it resumes on the
  next start ([`servicer-workflow-declare.md`](servicer-workflow-declare.md)).

## Scales as

- Not measured.

## Errors you will see

None known.

## See also

- [`api-errors.md`](api-errors.md) — the typed-error contract
- [`patterns-error-handling.md`](patterns-error-handling.md) — choosing declared errors
- [`servicer-workflow-external.md`](servicer-workflow-external.md) — failures as data
