---
title: Pick a Method Factory — `Reader`, `Writer`, `Transaction`, or `Workflow`
impact: CRITICAL
impactDescription: The factory drives the context type, isolation, and access semantics
tags: method, reader, writer, transaction, workflow, factory, constructor, mode, mcp, User
summary: "The factory fixes the servicer's context type, and `mcp=` is required; `Reader`/`Writer`/`Transaction`/`Workflow`, `factory=True`, `errors=`, `description=`."
step: api
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: ""
---

# Pick a Method Factory — `Reader`, `Writer`, `Transaction`, or `Workflow`

## When you are here

You are filling a `Methods(...)` block: per method, the factory, its
options, and the servicer method it obliges. Model/field rules:
[`api-pydantic.md`](api-pydantic.md); implementation: the matching
`servicer-*.md`.

## Do this

### Pick the factory

| Factory | Context | Use when |
| --- | --- | --- |
| `Reader(...)` | `ReaderContext` | Reading `self.state` only. Readers run concurrently. |
| `Writer(...)` | `WriterContext` | Mutating `self.state` of **one** actor; serialized with other writes on it. |
| `Transaction(...)` | `TransactionContext` | Mutating several actors atomically. Requires `mode=`. |
| `Workflow(...)` | `WorkflowContext` | Durable, long-running, restartable work, or any external call. A `@classmethod`; no `self.state`. Router: `servicer-workflow.md`. |

Every factory takes `request=`, `response=` (a `Model` or `None`),
optional `errors=[...]` ([`api-errors.md`](api-errors.md)), optional
`description=`, and a **required** `mcp=` (`None`, or `Tool()` to expose
an MCP tool).

`Transaction` `mode=` (both from `reboot.api`) sets how it locks its own state:
- `mode=Exclusive()` — exclusive from the start; concurrent callers
  queue. Use when it writes its own state (most transactions) or when
  in doubt.
- `mode=Shared()` — shared, upgraded only if the body writes its own
  state; callers proceed concurrently. Use when it mostly reads its own
  state while writing others (e.g. the root of a tree of states).

From [`reboot-bank-pydantic`](https://github.com/reboot-dev/reboot-bank-pydantic):

```python
from reboot.api import Methods, Shared, Transaction, Writer

AccountMethods = Methods(
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
        # Never writes the bank's own state, so transfers run concurrently.
        mode=Shared(),
        request=TransferRequest, response=TransferResponse,
        description="Move funds between two accounts, both sides "
        "landing together or neither.",
        mcp=None,
    ),
)
```

- `description=` shows in the dev dashboard and is the MCP tool
  description for `mcp=Tool()`. Write what the signature can't say:
  precondition, side effect, unit, which error and when, in short plain
  sentences ([`api-pydantic.md`](api-pydantic.md), "Writing a
  description"). Get it right
  before state persists: it is a frozen option, and rewording it later
  refuses boot ([`api-schema-evolution.md`](api-schema-evolution.md)).
- `factory=True` on a `Writer` or `Transaction` makes it the explicit
  creation path; the servicer branches on `context.constructor`
  ([`servicer-constructor.md`](servicer-constructor.md)). Without one,
  a `Type` is constructed implicitly on first write. To start a
  workflow on creation, schedule it from the factory's body.

### The Servicer Signature Each Declaration Obliges

`rbt generate` turns every entry into one method on `<Type>.Servicer`;
yours must match. This is the whole contract — don't read the generated
`*_rbt.py` (tens of thousands of lines):

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
`TaskList.AddTaskRequest`), never the class you passed (rule in
`api-pydantic.md`):

```python
# add_task=Transaction(mode=Exclusive(), request=AddTaskRequest, response=AddTaskResponse, mcp=None)
async def add_task(
    self,
    context: TransactionContext,
    request: TaskList.AddTaskRequest,
) -> TaskList.AddTaskResponse: ...

# lists=Reader(request=None, response=ListsResponse, mcp=None)
async def lists(self, context: ReaderContext) -> User.ListsResponse: ...

# ensure=Transaction(mode=Exclusive(), request=None, response=None, mcp=None)
async def ensure(self, context: TransactionContext) -> None: ...
```

Two generated shapes you do not write:
- A **PascalCase twin** (`AddTask` next to `add_task`) delegates to the
  snake_case one for older servicers; implement the snake_case method.
- A **`state:` parameter** (`(self, context, state, request)`) belongs
  to `<Type>.singleton.Servicer`, for framework singletons; subclass
  `<Type>.Servicer` and use `self.state`.

## Never

- `balance=BalanceResponse` (a bare `Model`) in `Methods(...)` — every
  entry must be a factory call.
- Omit `mcp=` — required on all four factories, `Workflow` included.
  Use `mcp=None`.
- `factory=True` on a `Reader` or `Workflow` — refused by
  `rbt generate`. Make the factory a `Writer`/`Transaction` and
  schedule the workflow from it.
- Choose `Writer` for a method that must change another actor — a writer
  mutates only its own actor (`servicer-writer.md`). Two types whose
  transactions write each other deadlock under concurrency; see
  `state-actor-decomposition.md` § Never.
- A sign-up method that creates `User`, an id passed to `useUser()`
  in the browser, or constructing `User` in tests — see Limits.
- `mcp=Resource()` — not supported; use `Tool()`.

## Limits

- Some entry names are reserved by the ref API and refused by codegen;
  the list is in [`rpc-refs.md`](rpc-refs.md) § Limits.
- A state type named exactly `User` is auto-constructed: with
  `Application(oauth=...)`, one `User` per signed-in identity on first
  access, state ID `context.auth.user_id`. A `User` type without
  `oauth=` fails to start.
  - Codegen injects `create` (`Transaction(factory=True)`) and
    `set_claims`; both are reserved — override them in the servicer,
    don't declare them.
  - Every `User` state field needs a default or `Optional`.
  - In tests, `rbt.create_external_context_as(name, user_id)` suffices
    for `User.ref(user_id)` to resolve.
  - Other types are constructed explicitly.

## Scales as

- Each kind's cost (a cross-actor transaction against a single-actor
  writer) is in `patterns-load-and-benchmarking.md`.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `Method '` … `' must be an instance of 'Writer', 'Reader', 'Transaction', 'Workflow', or 'UI'.` | An entry in `Methods(...)` is not a factory call | Wrap it in a factory |
| `Transaction '` … `' does not say how it holds the lock on its own state while it runs.` | `Transaction(...)` without `mode=` | Add `mode=Exclusive()` or `mode=Shared()` |
| `1 validation error for Workflow` / `mcp` / `Field required` | `mcp=` omitted (any factory; the first word names it) | Add `mcp=None` (or `mcp=Tool()` in an MCP UI) |
| `Error while parsing option value for "method": Message type "rbt.v1alpha1.WorkflowMethodOptions" has no field named "constructor".` | `factory=True` on a `Workflow` (or `Reader`) | Move `factory=True` to a `Writer`/`Transaction` |
| `'create' is a reserved method name for User types.` | `create` declared on `User` | Override `create` in the servicer instead |
| `'set_claims' is a reserved method name for User types` | `set_claims` declared on `User` | Override it in the servicer instead |
| `must have a default value, or be optional. User instances are auto-constructed` | A `User` state field lacks a default | Add a zero default or `Optional` |

## See also

- [`api-pydantic.md`](api-pydantic.md) — fields, defaults, generated names
- [`servicer-workflow.md`](servicer-workflow.md) — implementing a `Workflow`
- [`rpc-constructor-calls.md`](rpc-constructor-calls.md) — calling a `factory=True` method
