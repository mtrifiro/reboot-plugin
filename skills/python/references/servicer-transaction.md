---
title: Implement Transaction Methods
impact: HIGH
impactDescription: Cross-actor atomic work requires a transaction; an oversized or externally-calling one stalls, locks actors, or fires side effects twice
tags: servicer, transaction, TransactionContext, atomic, multi-actor, lock, participants, deadlock, two-phase commit
summary: "A transaction rolls back every mutation on every actor it touched; never call external systems inside one (schedule a workflow); oversized ones stall and lock actors."
step: servicer
applies: [mcp-ui, web-app, backend-only]
always: false
when: "you declared a `Transaction`"
verified: 1.6.0
docs: "https://docs.reboot.dev/develop/side_effects"
---

# Implement Transaction Methods

## When you are here

You are implementing a method declared `Transaction(...)` in the API
file: one that must change several actors all-or-nothing. A
transaction receives a `TransactionContext`; it is the only method
kind that can atomically mutate multiple actors, and it may also
mutate its own `self.state`. Durable multi-step work belongs in
`servicer-workflow.md`; the servicer signature codegen requires is in
`api-methods.md`. The public docs allow an idempotent side effect in
any method run as a task; this skill deliberately tightens that: an
external call goes in a `Workflow`, never in a transaction.

## Do this

The declaration's `mode=` says how the transaction holds the lock on
its own actor. `Exclusive()` takes it exclusive at the start, so
concurrent callers of that actor queue; choose it when the body writes
`state`. `Shared()` takes it shared and upgrades only if the body
writes `state`, so callers that only read proceed concurrently.

`api/bank/v1/bank.py` (from the
[`reboot-bank-pydantic`](https://github.com/reboot-dev/reboot-bank-pydantic)
example):

```python
transfer=Transaction(
    # The bank only coordinates: it reads nothing of its own state and
    # writes the accounts, so transfers proceed through it concurrently.
    mode=Shared(),
    request=TransferRequest,
    response=None,
    description="Move funds between two accounts, both sides landing "
    "together or neither.",
    mcp=None,
),
```

`main.py`:

```python
import asyncio
from bank.v1.account_rbt import Account
from bank.v1.bank_rbt import Bank
from reboot.aio.contexts import TransactionContext


class BankServicer(Bank.Servicer):

    async def transfer(
        self,
        context: TransactionContext,
        request: Bank.TransferRequest,
    ) -> None:
        from_account = Account.ref(request.from_account_id)
        to_account = Account.ref(request.to_account_id)

        await asyncio.gather(
            from_account.withdraw(context, amount=request.amount),
            to_account.deposit(context, amount=request.amount),
        )
```

If any call inside raises a `<Method>Aborted`, the runtime rolls back
**every** mutation the transaction made, on every actor it touched.
Reboot may retry the body internally, and in development re-runs it
for effect validation, so the body must be safe to run again with the
same input. Inside, you may call readers, writers, constructors and
other transactions (a nested transaction) on other actors;
`asyncio.gather` parallelizes the round trips of independent calls
(`Service.forall(ids)` fans one method out; `rpc-forall.md`).
`response=None` is valid: the method returns `-> None` with no
`return` (see `api-methods.md`).

### External calls: schedule a workflow

An email, payment, SMS or LLM call cannot be rolled back, and a retry
or effect-validation re-run would send it twice. Make the call in a
`Workflow` method (primitive per `servicer-workflow-external.md`) and reach it
only by scheduling:
`await self.ref().schedule().<workflow_method>(context)`. A call to an
in-system actor that itself schedules the external work is fine; the
bank's `sign_up` does exactly that:

```python
async def sign_up(
    self, context: TransactionContext, request: SignUpRequest,
) -> SignUpResponse:
    if mailgun_api_key := await self._mailgun_api_key():
        await mailgun.Message.send(
            context, None, Options(bearer_token=mailgun_api_key),
            recipient=request.account_id,
            sender='team@reboot.dev',
            domain='reboot.dev',
            subject='Welcome',
            html=self._html_email,
            text=self._text_email,
        )

    account, _ = await Account.open(context, request.account_id)
    await account.deposit(context, amount=request.initial_deposit)
    return SignUpResponse()
```

`mailgun.Message.send` is a `Writer` on an in-system actor that
schedules the HTTP send in a workflow; the transaction only issues
in-system RPCs.

## Never

- Multi-actor work in a `Writer` (`await Account.ref(a).withdraw(...)`
  then `deposit(...)`) — a writer mutates one actor. Use a transaction.
- An external call in the transaction body — it fires on abort and on
  every re-run. Schedule a workflow.
- Stash data on `self` — each call may get a fresh servicer instance.
  State lives in `self.state` or other actors.
- Wrap "do this to N things" in one transaction when N is more than a
  handful (48 showings stalled a suite; cineloop-40) — every actor is a
  two-phase-commit participant. Iterate in a `Workflow`, one small
  transaction or writer per item, `.per_workflow(f"... {id}")` per step.
- `schedule()` a method onto N foreign actors from one transaction —
  each becomes a 2PC participant; colliding prepares killed the dev
  database worker (theater-network-20, 1.4.0). Pass the list to a
  workflow and write each actor from there.
- Read an actor then write it as two calls — one writer that returns
  what the caller needs was about 10x faster under contention
  (theater-chain-17).
- Touch shared actors in different orders in different transactions
  (A then B here, B then A there) — they wait on each other. Keep one
  global touch order.
- Cancel in-flight transaction calls (load drivers, timing-out tests,
  Ctrl-C) — see Limits. Drain: stop issuing, await in-flight calls.
- Read `context.auth` in an actor called from this transaction — it is
  `None` there; pass identity in the request (`servicer-authorizer.md`).

## Limits

- A transaction holds locks on every actor it touches until it
  commits. Concurrent callers of those actors wait up to 30 s, then
  abort with `Unavailable` (`LOCK_ACQUIRE_DEADLINE_DEFAULT`, 1.6.0).
- Deadlocks between transactions are broken, not prevented: a
  transaction that waits more than 250 ms
  (`REBOOT_TRANSACTION_DEADLOCK_GRACE_MS`) on an actor held by an
  *older* transaction aborts with `TransactionShouldRetry` and is
  retried, keeping its first attempt's age (1.6.0 source). A plain
  reader or writer holding the lock never triggers this. Before 1.6.0,
  twelve concurrent bulk imports over shared actors stalled with no
  error (student-sor-05, 1.5.0).
- No documented size limit, but one is reachable: one transaction
  creating 138 actors plus `OrderedMap` inserts worked, 360 hung on
  lock waits and the app never came up (reboot-air-141-19, 1.4.1).
  Split seeds into transactions of a proven size, each with its own
  `.idempotently(alias)` (`lifecycle-initialize-hook.md`).
- A caller that vanished mid-transaction left its exclusive lock held
  until the application restarted; every later writer on that actor
  timed out, including sign-in, which writes `User` via `set_claims`
  (reboot-air-141-21, -load-02; observed 1.4.1, not re-tested at
  1.6.0). `rbt inspect` cannot show lock holders.
- A transaction cancelled during lock contention left one child actor
  constructed while its parent's side never committed (next run:
  `StateAlreadyConstructed`; student-sor-07, 1.5.0, cause undiagnosed).
- Subscribers see nothing until the whole transaction commits: a
  200-writer reset read as "hung"; batches of 25 gave progress
  (showtime-40).

## Scales as

- Cost grows with the number of **participants** (distinct actors),
  not calls: 8x fewer calls into the same participants bought 16%
  (theater-chain-18); about 10 sequential participants took about 10 s
  in the dev harness, about 4 took 2-3 s, and `asyncio.gather` does not
  lower the floor (reboot-bluesky-04, 1.4.1). A transaction is roughly
  5-10x a writer.
- N independent creations: 216 seats took 54 s as a transaction chain,
  15.7 s as a workflow of writer calls (theater-network-14, 1.4.0).
- A transaction holding a hot actor makes every user writer on it wait:
  bound background per-tick work (showtime-42).
- Full numbers and how to measure: `patterns-load-and-benchmarking.md`.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `Timed out waiting 30.0s to acquire exclusive lock; retry the transaction.` | Another holder kept the actor locked past the deadline (long transaction, or a vanished caller) | Shrink the transaction; drain callers; restart clears an orphaned lock |
| `Cannot upgrade shared lock to exclusive: another transaction is already upgrading the same state; retry the transaction.` | Two `Shared()` transactions both read then wrote (or scheduled on) the same actor | Use `Exclusive()`, or don't read before scheduling; give parallel chains their own actors |
| `is presumed deadlocked with it; aborting so that the older transaction proceeds. Retry required.` | Deadlock broken by aborting the younger transaction (logged; retried automatically) | Keep one actor-touch order to avoid the retries |
| `aborted with 'StateAlreadyConstructed'` | A constructor inside the transaction hit an existing actor | Probe first or construct via `.idempotently(...)` |

## See also

- [`servicer-workflow-external.md`](servicer-workflow-external.md) — external calls and N-item loops
- [`patterns-load-and-benchmarking.md`](patterns-load-and-benchmarking.md) — measured costs and method
- [`rpc-refs.md`](rpc-refs.md) — refs, existence probes, IDs
