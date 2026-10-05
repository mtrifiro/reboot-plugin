---
title: Use `Service.create` and `Service.<ctor>` for Constructor Calls
impact: MEDIUM
impactDescription: Calling a constructor through `.ref(...).method(...)` fails with `AttributeError`; a second call aborts `StateAlreadyConstructed`; a broad `except <X>Aborted` hides timeouts
tags: rpc, constructor, create, factory, StateAlreadyConstructed, get-or-create, Aborted
summary: "Call constructors as `<X>.<ctor>(context, id, ...)`, never through `.ref(id)`; `create` exists only if a factory is named that; outside a replayed key a second call aborts."
step: servicer
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: ""
---

# Use `Service.create` and `Service.<ctor>` for Constructor Calls

## When you are here

You need an actor of a type that declares a `factory=True` method to
come into existence, from a transaction, a workflow, `initialize`, a
test or an external client. Writing the constructor's body is in
`servicer-constructor.md`; calling ordinary methods is in `rpc-calls.md`.

## Do this

Every `factory=True` method is generated as a classmethod on the type,
under the method's own name. Call it with the context, the new actor's
id, and the request fields as kwargs. It returns a `(ref, response)`
tuple (`response` is `None` when the method declares `response=None`).
Use the returned ref for follow-up calls.

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

`main.py` (matches the [`reboot-bank-pydantic`](https://github.com/reboot-dev/reboot-bank-pydantic) example):

```python
account, _ = await Account.open(context, account_id)
await account.deposit(context, amount=request.initial_deposit)
```

`Bank.create(context, SINGLETON_BANK_ID)` is the same thing for a
factory method named `create`; there is no built-in `create`. A type
with **no** `factory=True` method has no constructor to call: its first
writer or transaction call constructs it implicitly (see
`lifecycle-initialize-hook.md`).

From `initialize`, a bare constructor call is safe to leave in place:
its persisted idempotency key replays the stored result on every later
boot, and the body does not run again (`lifecycle-initialize-hook.md`).

## Never

- `await Account.ref(account_id).open(context)` — constructors are not
  on the ref. mypy: `"WeakReference" has no attribute "open"`; at
  runtime `AttributeError: 'WeakReference' object has no attribute
  'open'` (observed at 1.6.0). Use `Account.open(context, account_id)`.
- `Lab.create(context, id)` on a type with no `factory=True` method —
  no `create` is generated (mypy: `"type[Lab]" has no attribute
  "create"`, showtime-32, 1.4.1; confirmed at 1.6.0). Call a writer.
- Calling a constructor a second time and expecting a no-op. Outside a
  key that was already used, it aborts with `StateAlreadyConstructed`;
  from a retrying workflow this loops forever (reboot-crm-68, 1.6.0).
  Get-or-create:

  ```python
  from rbt.v1alpha1.errors_pb2 import StateAlreadyConstructed

  try:
      logo, _ = await Logo.want(context, host)
  except Logo.WantAborted as aborted:
      if not isinstance(aborted.error, StateAlreadyConstructed):
          raise
      logo = Logo.ref(host)
  ```

- `except Seat.PlaceAborted: pass` around a constructor to tolerate
  "already exists". `<Method>Aborted` also carries system errors: a
  ping timeout under load arrived as `PlaceAborted` and was silently
  swallowed, leaving actors missing (theater-network-15, 1.4.0). Check
  `aborted.error` and re-raise anything else, as above.
- Stamping the caller's identity inside a constructor reached from
  another servicer — the nested call is app-internal and
  `context.auth` is `None`; pass the owner as a request field
  (reboot-crm-03, 1.6.0; `servicer-authorizer.md` § Never).

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
| `aborted with 'StateAlreadyConstructed'` | Constructor called on an existing actor | Get-or-create pattern above |
| `AttributeError: 'WeakReference' object has no attribute` | A constructor called through `Service.ref(id)` | `Service.<ctor>(context, id, ...)` |
| `has no attribute "create"` | No factory named `create` (or none at all) | Call the declared factory, or a writer on a factory-less type |
| `aborted with 'StateNotConstructed { requires_constructor: true }'` | Ordinary writer before the constructor ran | Call the constructor first |

## See also

- [`servicer-constructor.md`](servicer-constructor.md) — writing the constructor body
- [`rpc-refs.md`](rpc-refs.md) — probing whether an actor exists
- [`api-errors.md`](api-errors.md) — inspecting `aborted.error`
