---
title: Use `Service.create` and `Service.<ctor>` for Constructor Calls
impact: MEDIUM
impactDescription: Calling a constructor through `.ref(...).method(...)` fails with `AttributeError`; a second call aborts `StateAlreadyConstructed`; a broad `except <X>Aborted` hides timeouts
tags: rpc, constructor, create, factory, StateAlreadyConstructed, get-or-create, Aborted
summary: "Constructors aren't on `.ref(id)` and a second call aborts; call `<X>.<ctor>(context, id, ...)`; get-or-create."
step: servicer
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: ""
---

# Use `Service.create` and `Service.<ctor>` for Constructor Calls

## When you are here

Bringing into existence an actor whose type declares a `factory=True`
method, from a transaction, workflow, `initialize`, test or external
client. Constructor body: `servicer-constructor.md`; ordinary calls:
`rpc-calls.md`.

## Do this

Each `factory=True` method is a classmethod on the type under its own
name. Pass the context, the new id, and request fields as kwargs; it
returns `(ref, response)` (`response` is `None` for `response=None`).
Use the returned ref for follow-up calls.

```python
# api/bank/v1/account.py: open=Writer(request=OpenRequest, response=None, factory=True, ...)
# main.py, matches the reboot-bank-pydantic example
# (https://github.com/reboot-dev/reboot-bank-pydantic):
account, _ = await Account.open(context, account_id)
await account.deposit(context, amount=request.initial_deposit)
```

- `Bank.create(context, SINGLETON_BANK_ID)` is the same for a factory
  named `create`; there is no built-in `create`.
- A type with **no** `factory=True` method has no constructor: its
  first writer or transaction call constructs it implicitly.
- A bare constructor call in `initialize` is safe to leave: its
  persisted idempotency key replays the stored result every later boot
  and the body does not rerun (`lifecycle-initialize-hook.md`).

## Never

- `await Account.ref(account_id).open(context)` — constructors are not
  on the ref. mypy: `"WeakReference" has no attribute "open"`; runtime:
  `AttributeError: 'WeakReference' object has no attribute 'open'`
  (observed at 1.6.0).
- `Lab.create(context, id)` on a type with no `factory=True` method —
  not generated (mypy: `"type[Lab]" has no attribute "create"`,
  showtime-32, 1.4.1; confirmed at 1.6.0). Call a writer.
- Expecting a second constructor call to be a no-op. Outside an
  already-used key it aborts `StateAlreadyConstructed`, whatever the
  constructor branches on (`context.constructor` changes nothing); a
  retrying workflow loops forever (reboot-crm-68, 1.6.0). A used key
  (`initialize`'s automatic per-(actor, method) key, or a repeated
  `.idempotently(alias)`) returns the memoized result without running
  the body. Get-or-create:

  ```python
  from rbt.v1alpha1.errors_pb2 import StateAlreadyConstructed

  try:
      logo, _ = await Logo.want(context, host)
  except Logo.WantAborted as aborted:
      if not isinstance(aborted.error, StateAlreadyConstructed):
          raise
      logo = Logo.ref(host)
  ```

- `except Seat.PlaceAborted: pass` to tolerate "already exists" —
  `<Method>Aborted` also carries system errors: a ping timeout under
  load arrived as `PlaceAborted` and was swallowed, leaving actors
  missing (theater-network-15, 1.4.0). Check `aborted.error` and
  re-raise the rest, as above.
- Stamping caller identity in a constructor reached from another
  servicer — `context.auth` is `None` there; pass the owner as a
  request field (reboot-crm-03, 1.6.0; `servicer-authorizer.md` § Never).

## Limits

- Callable from `TransactionContext`, `WorkflowContext` and
  `ExternalContext` (including `InitializeContext`) only; not from a
  reader or writer (generated signature, 1.6.0).
- Not available through `Service.forall(ids)`, and constructors cannot
  be scheduled (1.6.0 template).
- On a type with a factory, any non-constructor writer on a missing
  actor aborts with `StateNotConstructed { requires_constructor: true }`
  (`rpc-refs.md`).

## Scales as

- A constructor call costs the same as any mutating call; in dev,
  effect validation runs it twice (`patterns-load-and-benchmarking.md`).

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `aborted with 'StateAlreadyConstructed'` | Explicit constructor called on an existing actor (e.g. `OpenAborted: aborted with 'StateAlreadyConstructed'`), also inside a transaction | Get-or-create pattern above (probe first), or construct via `.idempotently(...)` / `initialize`'s key |
| `AttributeError: 'WeakReference' object has no attribute` | A constructor called through `Service.ref(id)` | `Service.<ctor>(context, id, ...)` |
| `has no attribute "create"` | No factory named `create` (or none at all) | Call the declared factory, or a writer on a factory-less type |

## See also

- [`servicer-constructor.md`](servicer-constructor.md) — writing the constructor body
- [`rpc-refs.md`](rpc-refs.md) — probing whether an actor exists
- [`api-errors.md`](api-errors.md) — inspecting `aborted.error`
