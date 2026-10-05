---
title: Implement Transaction Methods
impact: HIGH
impactDescription: Cross-actor atomic work requires a transaction; an oversized or externally-calling one stalls, locks actors, or fires side effects twice
tags: servicer, transaction, TransactionContext, atomic, multi-actor, lock, participants, deadlock, two-phase commit
summary: "External calls inside fire on abort; oversized transactions stall; rollback spans every touched actor; schedule a workflow instead."
step: servicer
applies: [mcp-ui, web-app, backend-only]
always: false
when: "you declared a `Transaction`"
verified: 1.6.0
docs: "https://docs.reboot.dev/develop/side_effects"
---

# Implement Transaction Methods

## When you are here

Implementing a method declared `Transaction(...)`: it takes a
`TransactionContext` and is the only kind that atomically mutates
several actors (plus its own `self.state`). Durable multi-step work:
`servicer-workflow.md`; exact signature: `api-methods.md`. The public
docs allow an idempotent side effect in any method run as a task; this
skill deliberately tightens that: an external call goes in a
`Workflow`, never in a transaction.

## Do this

`mode=` sets the lock on its own actor: `Exclusive()` takes it
exclusive at the start (concurrent callers queue), for bodies that
write `state`; `Shared()` takes it shared and upgrades only if the body
writes `state`, so read-only callers proceed concurrently.

From the [`reboot-bank-pydantic`](https://github.com/reboot-dev/reboot-bank-pydantic) example:

```python
# api/bank/v1/bank.py:
#   transfer=Transaction(mode=Shared(), request=TransferRequest, response=None, ...)
#   Shared(): the bank only coordinates, writing accounts, not its own state.
import asyncio
from bank.v1.account_rbt import Account
from bank.v1.bank_rbt import Bank
from reboot.aio.contexts import TransactionContext


class BankServicer(Bank.Servicer):

    async def transfer(
        self,
        context: TransactionContext,
        request: Bank.TransferRequest,
    ) -> None:  # response=None: no return (api-methods.md)
        from_account = Account.ref(request.from_account_id)
        to_account = Account.ref(request.to_account_id)

        await asyncio.gather(
            from_account.withdraw(context, amount=request.amount),
            to_account.deposit(context, amount=request.amount),
        )
```

- Any `<Method>Aborted` inside rolls back **every** mutation on every
  actor touched.
- Reboot may retry the body, and in development re-runs it for effect
  validation: it must be safe to rerun with the same input.
- Inside, call readers, writers, constructors and other transactions
  (nested) on other actors; `asyncio.gather` parallelizes independent
  round trips; `Service.forall(ids)` fans one method out
  (`rpc-forall.md`).

### External calls: schedule a workflow

An email, payment, SMS or LLM call cannot be rolled back and a re-run
sends it twice. Put it in a `Workflow` method (primitive per
`servicer-workflow-external.md`) reached only by
`await self.ref().schedule().<workflow_method>(context)`. Calling an
in-system actor that itself schedules the external work is fine: the
bank's `sign_up` calls `await mailgun.Message.send(context, None,
Options(bearer_token=mailgun_api_key), recipient=..., ...)`, a `Writer`
on an in-system actor that schedules the HTTP send in a workflow, then
`Account.open(...)`.

## Never

- Multi-actor work in a `Writer` (`withdraw(...)` then `deposit(...)`
  on other actors) — a writer mutates one actor.
- An external call in the body — it fires on abort and every re-run.
- Stash data on `self` — each call may get a fresh servicer instance;
  state lives in `self.state` or other actors.
- One transaction over N things when N is more than a handful (Reset
  All over 48 showings stalled a suite; cineloop-40, 1.4.1) — every actor is a two-phase-
  commit participant. Iterate in a `Workflow`, one small transaction or
  writer per item, `.per_workflow(f"... {id}")` per step.
- `schedule()` onto N foreign actors from one transaction — each
  becomes a 2PC participant; colliding prepares killed the dev database
  worker (`database.cc:1374` assert; theater-network-20, 1.4.0). Pass
  the list in a workflow's request and write each actor from the
  workflow.
- Read an actor then write it as two calls — one writer returning what
  the caller needs was about 10x faster under contention
  (theater-chain-17).
- Touch shared actors in different orders in different transactions
  (A then B, B then A) — they wait on each other. Keep one global order.
- Cancel in-flight transaction calls (load drivers, timing-out tests,
  Ctrl-C) — see Limits. Drain: stop issuing, await in-flight calls.
- Read `context.auth` in an actor called from this transaction — it is
  `None`; pass identity in the request (`servicer-authorizer.md`).

## Limits

- Locks on every touched actor are held until commit; concurrent
  callers wait up to 30 s, then abort with `Unavailable` (`LOCK_ACQUIRE_DEADLINE_DEFAULT`, 1.6.0).
- Deadlocks between transactions are broken, not prevented: a
  transaction that waits more than 250 ms
  (`REBOOT_TRANSACTION_DEADLOCK_GRACE_MS`) on an actor held by an
  *older* transaction aborts with `TransactionShouldRetry` and is
  retried, keeping its first attempt's age (1.6.0 source); a plain
  reader or writer holding the lock never triggers this. Before 1.6.0,
  twelve concurrent bulk imports over shared actors stalled with no
  error (student-sor-05, 1.5.0).
- No documented size limit, but one is reachable: creating 138 actors
  plus `OrderedMap` inserts worked, 360 hung on lock waits and the app
  never came up (reboot-air-141-19, 1.4.1). Split seeds into proven-size
  transactions, each with its own `.idempotently(alias)`
  (`lifecycle-initialize-hook.md`).
- A caller that vanished mid-transaction left its exclusive lock held
  until restart; every later writer on that actor timed out, including
  sign-in (writes `User` via `set_claims`)
  (reboot-air-141-21, -load-02; observed 1.4.1, not re-tested at
  1.6.0). `rbt inspect` cannot show lock holders.
- A transaction cancelled during lock contention left one child actor
  constructed while its parent's side never committed (next run:
  `StateAlreadyConstructed`; student-sor-07, 1.5.0, cause undiagnosed).
- Subscribers see nothing until commit: a 200-writer reset read as
  "hung"; batches of 25 gave progress
  (showtime-40).

## Scales as

- Cost grows with **participants** (distinct actors), not calls: 8x
  fewer calls into the same participants bought 16% (theater-chain-18);
  about 10 sequential participants took about 10 s in the dev harness,
  about 4 took 2-3 s; `asyncio.gather` does not lower the floor (reboot-bluesky-04, 1.4.1). A transaction is roughly
  5-10x a writer.
- N independent creations: 216 seats took 54 s as a transaction chain,
  15.7 s as a workflow of writer calls (theater-network-14, 1.4.0).
- A transaction on a hot actor stalls every user writer on it: bound
  background per-tick work (showtime-42).
- Full numbers and how to measure: `patterns-load-and-benchmarking.md`.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `Timed out waiting 30.0s to acquire exclusive lock; retry the transaction.` | Another holder kept the actor locked past the deadline (long transaction, or a vanished caller) | Shrink the transaction; drain callers; restart clears an orphaned lock |
| `Cannot upgrade shared lock to exclusive: another transaction is already upgrading the same state; retry the transaction.` | Two `Shared()` transactions both read then wrote (or scheduled on) the same actor | Use `Exclusive()`, or don't read before scheduling; give parallel chains their own actors |
| `is presumed deadlocked with it; aborting so that the older transaction proceeds. Retry required.` | Deadlock broken by aborting the younger transaction (logged; retried automatically) | Keep one actor-touch order to avoid the retries |

## See also

- [`servicer-workflow-external.md`](servicer-workflow-external.md) — external calls and N-item loops
- [`patterns-load-and-benchmarking.md`](patterns-load-and-benchmarking.md) — measured costs and method
- [`rpc-refs.md`](rpc-refs.md) — refs, existence probes, IDs
