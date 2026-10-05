---
title: Pick a Method Factory — `Reader`, `Writer`, `Transaction`, or `Workflow`
impact: CRITICAL
impactDescription: The factory drives the context type, isolation, and access semantics
tags: method, reader, writer, transaction, workflow, factory, constructor, mode, mcp, User
summary: "Which factory (`Reader`, `Writer`, `Transaction`, `Workflow`) and the servicer signature and context type each obliges; `factory=True` marks creation; `errors=`, `description=` and the required `mcp=`."
step: api
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: ""
---

# Pick a Method Factory — `Reader`, `Writer`, `Transaction`, or `Workflow`

## When you are here

You are filling a `Methods(...)` block and choosing, per method, the
factory, its options, and therefore the servicer method you must
write. Model and field rules are in [`api-pydantic.md`](api-pydantic.md);
how each kind is implemented is in the matching `servicer-*.md`.

## Do this

### Pick the factory

| Factory | Context | Use when |
| --- | --- | --- |
| `Reader(...)` | `ReaderContext` | Reading `self.state` only. Readers run concurrently. |
| `Writer(...)` | `WriterContext` | Mutating `self.state` of **one** actor; serialized with other writes on it. |
| `Transaction(...)` | `TransactionContext` | Mutating several actors atomically. Requires `mode=`. |
| `Workflow(...)` | `WorkflowContext` | Durable, long-running, restartable work, or any external call. A `@classmethod`; no `self.state`. Router: `servicer-workflow.md`. |

Every factory takes `request=`, `response=` (a `Model` or `None`),
optional `errors=[...]` (typed errors; raising them is in
[`api-errors.md`](api-errors.md)), optional `description=`, and a
**required** `mcp=` (`None`, or `Tool()` to expose it as an MCP tool).

A `Transaction` must also declare how it holds the lock on its own
state: `mode=Exclusive()` takes it exclusive from the start, so
concurrent callers of the same state queue: the choice when it writes
its own state, which is most transactions, and when in doubt.
`mode=Shared()` takes it shared and upgrades only if the body writes
its own state, so callers proceed concurrently: the choice for a
transaction that mostly reads its own state while writing others, such
as the root of a tree of states. Both import from `reboot.api`.

From [`reboot-bank-pydantic`](https://github.com/reboot-dev/reboot-bank-pydantic):

```python
from reboot.api import (
    API, Exclusive, Field, Methods, Model, Reader, Shared, Transaction, Type,
    Writer,
)

AccountMethods = Methods(
    balance=Reader(
        request=None, response=BalanceResponse,
        description="The funds currently available to withdraw.",
        mcp=None,
    ),
    deposit=Writer(
        request=DepositRequest, response=None,
        description="Add funds. Any amount is accepted.",
        mcp=None,
    ),
    withdraw=Writer(
        request=WithdrawRequest, response=None,
        errors=[OverdraftError],
        description="Take funds out, or raise `OverdraftError` if the "
        "balance would go negative.",
        mcp=None,
    ),
    open=Writer(
        request=None, response=None,
        factory=True,
        description="Bring the account into existence with a zero balance.",
        mcp=None,
    ),
)

BankMethods = Methods(
    transfer=Transaction(
        # The bank only coordinates the two accounts and never writes
        # its own state, so transfers proceed through it concurrently.
        mode=Shared(),
        request=TransferRequest, response=TransferResponse,
        description="Move funds between two accounts, both sides "
        "landing together or neither.",
        mcp=None,
    ),
)
```

`description=` is shown by the dev dashboard and used as the MCP tool
description for `mcp=Tool()` methods. Write what a caller cannot
derive from the signature: the precondition, the side effect, the
unit, which error it raises and when. Get it right before state
persists: a method's `description=` is part of its frozen options, and
rewording it later refuses boot
([`api-schema-evolution.md`](api-schema-evolution.md)).

`factory=True` on a `Writer` or `Transaction` makes it the actor's
explicit creation path; the servicer branches on `context.constructor`
([`servicer-constructor.md`](servicer-constructor.md)). A `Type`
without one is constructed implicitly on first write. To start a
workflow when an actor is created, schedule it from the factory's
body.

### The Servicer Signature Each Declaration Obliges

`rbt generate` turns every entry into one method on
`<Type>.Servicer`, and yours must match it. This is the whole
contract; there is nothing more to learn from the generated
`*_rbt.py`, which runs to tens of thousands of lines:

```python
class AnyNameServicer(<Type>.Servicer):    # subclass this alias

    # `@classmethod`, for a `Workflow(...)` method only.
    async def <entry_name>(                # snake_case, as declared
        self,                              # `cls` for a `Workflow`
        context: <Kind>Context,            # per the factory, above
        request: <Type>.<Entry>Request,   # omitted if `request=None`
    ) -> <Type>.<Entry>Response:          # `None` if `response=None`
```

`<Entry>` is the PascalCase entry name (`add_task` on `TaskList` gives
`TaskList.AddTaskRequest`), never the class you passed; the rule is in
`api-pydantic.md`. So

```python
add_task=Transaction(
    mode=Exclusive(),
    request=AddTaskRequest, response=AddTaskResponse,
    description="Append one task, returning the id it was given.",
    mcp=None,
),
lists=Reader(
    request=None, response=ListsResponse,
    description="Every list this user owns.",
    mcp=None,
),
ensure=Transaction(
    mode=Exclusive(),
    request=None, response=None,
    description="Create the user's default list if they have none.",
    mcp=None,
),
```

obliges exactly:

```python
async def add_task(
    self,
    context: TransactionContext,
    request: TaskList.AddTaskRequest,
) -> TaskList.AddTaskResponse: ...

async def lists(self, context: ReaderContext) -> User.ListsResponse: ...

async def ensure(self, context: TransactionContext) -> None: ...
```

Two shapes in the generated file look like contradictions; neither is
what you write. A **PascalCase twin** of every method (`AddTask` next
to `add_task`) delegates to the snake_case one for older servicers:
implement the snake_case method. A **`state:` parameter**
(`(self, context, state, request)`) belongs to
`<Type>.singleton.Servicer`, which the framework uses for its own
singletons; applications subclass `<Type>.Servicer` and use
`self.state`.

## Never

- `balance=BalanceResponse` (a bare `Model`) in `Methods(...)` — every
  entry must be a factory call.
- Omit `mcp=` — required on all four factories, `Workflow` included,
  though workflows are rarely tools. Use `mcp=None`.
- `factory=True` on a `Reader` or `Workflow` — refused by
  `rbt generate`. Make the factory a `Writer`/`Transaction` and
  schedule the workflow from it.
- Choose `Writer` for a method that must change another actor — a
  writer mutates only its own actor (`servicer-writer.md`). And two
  types whose transactions write each other deadlock under concurrent
  requests; see `state-actor-decomposition.md` § Never.
- A sign-up method that creates `User`, an id passed to `useUser()`
  in the browser, or constructing `User` in tests — see Limits.
- `mcp=Resource()` — not supported; use `Tool()`.

## Limits

- Some entry names are reserved by the ref API and refused by codegen;
  the list is in [`rpc-refs.md`](rpc-refs.md) § Limits.
- A state type named exactly `User` is auto-constructed: with
  `Application(oauth=...)`, Reboot constructs one `User` per signed-in
  identity on first access, with state ID `context.auth.user_id`.
  Codegen injects `create` (`Transaction(factory=True)`) and
  `set_claims`; both names are reserved on `User` — override them in
  the servicer for custom initialization, don't declare them. Every
  `User` state field needs a default or `Optional`. In tests,
  `rbt.create_external_context_as(name, user_id)` is enough for
  `User.ref(user_id)` to resolve. An app with a `User` type and no
  `oauth=` fails to start. Other types are constructed explicitly.
- The context type follows the factory (table above); annotate the
  one it names.

## Scales as

- Each kind's cost (a cross-actor transaction against a single-actor
  writer) is in `patterns-load-and-benchmarking.md`.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `Method '` … `' must be an instance of 'Writer', 'Reader', 'Transaction', 'Workflow', or 'UI'.` | An entry in `Methods(...)` is not a factory call | Wrap it in a factory |
| `Transaction '` … `' does not say how it holds the lock on its own state while it runs.` | `Transaction(...)` without `mode=` | Add `mode=Exclusive()` or `mode=Shared()` |
| `1 validation error for Workflow` / `mcp` / `Field required` | `mcp=` omitted (any factory; the first word names it) | Add `mcp=None` |
| `Error while parsing option value for "method": Message type "rbt.v1alpha1.WorkflowMethodOptions" has no field named "constructor".` | `factory=True` on a `Workflow` (or `Reader`) | Move `factory=True` to a `Writer`/`Transaction` |
| `'create' is a reserved method name for User types.` | `create` declared on `User` | Override `create` in the servicer instead |
| `'set_claims' is a reserved method name for User types` | `set_claims` declared on `User` | Override it in the servicer instead |
| `must have a default value, or be optional. User instances are auto-constructed` | A `User` state field lacks a default | Add a zero default or `Optional` |
| `'Resource()' is not yet supported; use 'Tool()' instead` | `mcp=Resource()` | Use `mcp=Tool()` |

## See also

- [`api-pydantic.md`](api-pydantic.md) — fields, defaults, generated names
- [`servicer-workflow.md`](servicer-workflow.md) — implementing a `Workflow`
- [`rpc-constructor-calls.md`](rpc-constructor-calls.md) — calling a `factory=True` method
