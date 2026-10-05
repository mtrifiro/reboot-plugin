---
title: API Definition — Method Types and Tool Exposure
impact: CRITICAL
impactDescription: The pydantic API file is the source of truth for both Reboot codegen AND MCP tool surface. `UI()` is MCP-UI-only; every method (including `User`'s) requires explicit `mcp=`; application types need `factory=True` on their `create` Writer.
tags: api, pydantic, ui, tool, mcp, reader, writer, transaction, workflow, factory, user
summary: "Every method, `Workflow` included, needs explicit `mcp=Tool()` or `mcp=None`; put an entity's `UI()` on that entity's Type, never on `User` with an ID in `request=`; `factory=True` on `create`."
step: api
applies: [mcp-ui]
always: false
verified: 1.6.0
docs: ""
---

# API Definition — Method Types and Tool Exposure

## When you are here

You are writing the pydantic API file of an MCP UI: a `User` front-door
type plus one `Type` per application entity, deciding which methods the
AI may call and where each `UI()` goes. This file is only the MCP-UI
delta. The generic rules — zero-value defaults, `Optional[X] = None` for
a nested `Model`, field tags, generated `<Type>.<Method>Request` names —
are in
[`api-pydantic.md`](../../python/references/api-pydantic.md); which
factory to pick and the servicer signature each obliges are in
[`api-methods.md`](../../python/references/api-methods.md).

## Do this

```python
from reboot.api import (
    API,
    Exclusive,
    UI,
    Field,
    Methods,
    Model,
    Reader,
    Tool,
    Transaction,
    Type,
    Writer,
)


# -- User models. --


class CreateCounterResponse(Model):
    counter_id: str = Field(tag=1, default="")


class UserState(Model):
    pass


# -- Counter models. --


class CounterState(Model):
    value: int = Field(tag=1, default=0)
    description: str = Field(tag=2, default="")


class ValueResponse(Model):
    value: int = Field(tag=1, default=0)


class AmountRequest(Model):
    """Request with an amount parameter."""
    amount: int = Field(tag=1, default=0)


api = API(
    User=Type(
        state=UserState,
        methods=Methods(
            create_counter=Transaction(
                mode=Exclusive(),
                request=None,
                response=CreateCounterResponse,
                description="Create a new Counter. Returns the ID of "
                "the new counter. That ID is not human-readable; "
                "pass it to future tool calls where needed, but no "
                "need to tell the human what it is.",
                mcp=Tool(),
            ),
        ),
    ),
    Counter=Type(
        state=CounterState,
        # What the state type is for, shown by the dev dashboard
        # beside its name and file.
        description="One counter the user created, and the "
        "consistency boundary its value changes on.",
        methods=Methods(
            # `show_clicker` lives on `Counter` (not `User`)
            # because it shows ONE specific Counter. The AI calls
            # the generated `counter_show_clicker` tool with the
            # target Counter's state ID; the React hook resolves
            # that ID automatically.
            show_clicker=UI(
                request=None,
                path="frontend/mcp/clicker",
                title="Counter Clicker",
                description="Interactive clicker UI for the counter.",
            ),
            # Not an MCP tool, and still worth describing: the dev
            # dashboard shows `description=` for every method.
            create=Writer(
                request=None,
                response=None,
                factory=True,
                description="Create the counter at zero.",
                mcp=None,
            ),
            get=Reader(
                request=None,
                response=ValueResponse,
                description="Get the current counter value.",
                mcp=Tool(),
            ),
            increment=Writer(
                request=AmountRequest,
                response=None,
                description="Increment the counter by the specified amount.",
                mcp=Tool(),
            ),
            decrement=Writer(
                request=AmountRequest,
                response=None,
                description="Decrement the counter by the specified amount.",
                mcp=Tool(),
            ),
        ),
    ),
)
```

The shape, piece by piece:

- **`User` is the front door.** Empty (or near-empty) state, and a
  `Transaction` per application type that creates an instance and
  returns its ID (servicer side:
  [`servicer-patterns.md`](servicer-patterns.md)).
- **`factory=True` on each application type's `create` Writer.** That
  is what generates the `Counter.create(context)` the `User` transaction
  calls (mechanics:
  [`servicer-constructor.md`](../../python/references/servicer-constructor.md)).
- **Every method states its exposure.** `mcp=Tool()` makes it an
  AI-callable tool, on `User` as on every other type; `mcp=None` hides
  it (human-only actions, or to keep the AI's tool list small).
  `Tool(name="...", title="...")` overrides the tool name or adds a
  human-readable title. The tool's description is the method's
  `description=`. `Workflow(...)` needs `mcp=` too, usually `None`.
- **`UI()` opens a React UI inside the MCP host.** It takes `request=`
  (a config `Model` or `None`), `path=` (the UI's web directory,
  relative to the project root, e.g. `"frontend/mcp/clicker"`),
  `title=`, `description=`. It has no servicer implementation — the
  React app is the implementation.

### Where a `UI()` goes

Ask: "is the AI handing this UI an entity ID to operate on?"

- **Yes** ("show this Person", "edit this Task") → `UI(request=None)`
  on that entity's `Type`. The generated tool takes that Type's state ID
  as its target, and the UI's zero-argument `use<Type>()` hook resolves
  it ([`react-app-tsx.md`](react-app-tsx.md)). The AI calls
  `person_show(person_id=...)` and the UI materializes for exactly that
  Person.
- **No, it is user-scoped** ("my dashboard", "browse all my Persons") →
  `UI()` on `User`.
- **It takes free-form config the AI fills in** (a personalization
  string, a layout hint) → `request=<Model>` on whichever Type the UI
  belongs to. The `Model`'s fields arrive as props on the React
  component (camelCased):

```python
class DashboardConfig(Model):
    """Configuration the AI provides when opening the dashboard."""
    personalized_message: str = Field(tag=1, default="")


# On `Counter`: the Counter ID is still the implicit tool-call target;
# `request=` carries only the personalization string.
show_dashboard=UI(
    request=DashboardConfig,
    path="frontend/mcp/dashboard",
    title="Counter Dashboard",
    description="Dashboard UI. Use `personalized_message` to impart "
    "wisdom on the topic of counting things.",
),
```

```tsx
export const DashboardApp: FC<DashboardConfig> = ({ personalizedMessage }) => {
  // No `id` argument — resolved from the tool-call target. The handle
  // is `undefined` until it resolves; see `react-app-tsx.md`.
  const { counter } = useCounter();
  return counter && (
    <CounterValue counter={counter} label={personalizedMessage} />
  );
};
```

"The User is the front door" is about **creating and locating**
entities. Once the AI holds an entity's ID, everything specific to that
entity — Readers, Writers, UIs — goes on that entity's `Type`.

## Never

- `show_person=UI(request=ShowPersonProps)` on `User`, where
  `ShowPersonProps` carries `person_id: str` — the AI must plumb the ID
  through a tool input where it can confuse it with another entity's
  ID, the component must call `usePerson({ id: personId })` by hand, and
  the UI sits apart from every other per-Person method; in MCPJam it
  shows up as a tool with a leaky entity-ID input. Put
  `show=UI(request=None, path="frontend/mcp/person", ...)` on `Person`.
  Entity IDs never belong in a `request=<Model>` field.
- A method with no `mcp=` — not even `Workflow`, which is easy to miss
  because workflows are rarely AI-callable. Codegen rejects it; write
  `mcp=None`.
- An application type whose `create` Writer lacks `factory=True` — no
  `create` is generated, so the `User` front-door transaction has
  nothing to call.
- `UI(path=...)` without `request=` — `request` has no default; write
  `request=None` for a UI with no props.
- `UI(path="mcp/clicker")` or an absolute path — `path=` is relative to
  the project root: `"frontend/mcp/<name>"`.
- `mcp=Resource()` — rejected at 1.6.0; use `Tool()`.

## Limits

- `Tool` has only `name` and `title` (1.6.0 `reboot/api.py`); generated
  tools carry no MCP annotations (`readOnlyHint` etc.), so a host such as
  Claude asks permission before every call, Readers included, and
  "Always allow" is per tool. No application-side workaround (reboot-crm,
  1.6.0).
- `UI()` has no `response=` and no servicer method.

## Scales as

- Every `mcp=Tool()` method adds a tool to the AI's context; hide
  UI-only and human-only methods with `mcp=None`.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `1 validation error for Workflow` / `mcp` / `Field required` | A factory (any of the four) declared without `mcp=` | Add `mcp=None` or `mcp=Tool()` |
| `1 validation error for UI` / `request` / `Field required` | `UI()` without `request=` | `request=None` |
| `'Resource()' is not yet supported; use 'Tool()' instead` | `mcp=Resource()` | `mcp=Tool()` |
| `"type[<Type>]" has no attribute "create"` | mypy: the type has no `factory=True` method (observed at 1.4.1) | `factory=True` on its `create` Writer |
| `AttributeError: type object '<Type>' has no attribute '<WrongName>'` | Request/response referenced by source class name | `<Type>.<MethodPascalCase>Request` — see [`api-pydantic.md`](../../python/references/api-pydantic.md) |

## See also

- [`servicer-patterns.md`](servicer-patterns.md) — implementing the `User` front door
- [`react-app-tsx.md`](react-app-tsx.md) — the UI's zero-arg hook
- [`api-methods.md`](../../python/references/api-methods.md) — factory choice, servicer signatures
