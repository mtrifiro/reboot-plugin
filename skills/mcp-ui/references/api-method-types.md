---
title: API Definition — Method Types and Tool Exposure
impact: CRITICAL
impactDescription: The pydantic API file is the source of truth for both Reboot codegen AND MCP tool surface. `UI()` is MCP-UI-only; every method (including `User`'s) requires explicit `mcp=`; application types need `factory=True` on their `create` Writer.
tags: api, pydantic, ui, tool, mcp, reader, writer, transaction, workflow, factory, user
summary: "Every method needs `mcp=Tool()` or `mcp=None`; an entity's `UI()` goes on its Type, not `User`; `factory=True` `create`."
step: api
applies: [mcp-ui]
always: false
verified: 1.6.0
docs: ""
---

# API Definition — Method Types and Tool Exposure

## When you are here

Writing an MCP UI's pydantic API: a `User` front-door type plus one `Type`
per application entity, choosing AI-callable methods and where each `UI()`
goes. MCP-UI delta only; generic rules (zero-value defaults,
`Optional[X] = None` for a nested `Model`, field tags,
`<Type>.<Method>Request` names) are in
[`api-pydantic.md`](../../python/references/api-pydantic.md); factory
choice and servicer signatures in
[`api-methods.md`](../../python/references/api-methods.md).

## Do this

```python
from reboot.api import (
    API, Exclusive, UI, Field, Methods, Model, Reader, Tool, Transaction,
    Type, Writer,
)


class CreateCounterResponse(Model):
    counter_id: str = Field(
        tag=1, default="",
        description="The new counter's state id, for later tool calls.",
    )


class UserState(Model):
    pass


class CounterState(Model):
    value: int = Field(tag=1, default=0, description="The current count.")
    description: str = Field(
        tag=2, default="", description="What this counter counts, as the user said it.",
    )


class ValueResponse(Model):
    value: int = Field(tag=1, default=0, description="The count when read.")


class AmountRequest(Model):
    amount: int = Field(tag=1, default=0, description="How much to change the count by.")


api = API(
    User=Type(
        state=UserState,
        methods=Methods(
            create_counter=Transaction(
                mode=Exclusive(),
                request=None,
                response=CreateCounterResponse,
                description="Create a new counter and return its ID. "
                "The ID is not meant for people. Pass it to later tool "
                "calls instead of showing it to the user.",
                mcp=Tool(),
            ),
        ),
    ),
    Counter=Type(
        state=CounterState,
        # Shown by the dev dashboard beside the type's name.
        description="One counter the user created, and the "
        "consistency boundary its value changes on.",
        methods=Methods(
            # On `Counter`, not `User`: it shows ONE Counter. The AI calls
            # `counter_show_clicker` with the Counter's state ID; the
            # React hook resolves it.
            show_clicker=UI(
                request=None,
                path="frontend/mcp/clicker",
                title="Counter Clicker",
                description="Interactive clicker UI for the counter.",
            ),
            # Not a tool; `description=` still shows in the dashboard.
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

- **`User` is the front door**: empty state, one `Transaction` per
  application type that creates an instance and returns its ID
  ([`servicer-patterns.md`](servicer-patterns.md)).
- **`factory=True` on each type's `create` Writer** generates the
  `Counter.create(context)` the `User` transaction calls
  ([`servicer-constructor.md`](../../python/references/servicer-constructor.md)).
- **Every method states exposure**, `User`'s and `Workflow(...)`
  included: `mcp=Tool()` makes an AI-callable tool (its description is
  the method's `description=`); `mcp=None` hides it (human-only, or to
  keep the tool list small). `Tool(name="...", title="...")` overrides
  the name or adds a title.
- **`UI()` opens a React UI in the MCP host**: `request=` (config `Model`
  or `None`), `path=` (relative to the project root, e.g.
  `"frontend/mcp/clicker"`), `title=`, `description=`. No servicer: the
  React app is the implementation.

### Where a `UI()` goes

- **The AI hands it an entity ID** ("show this Person") →
  `UI(request=None)` on that entity's `Type`. The tool takes that Type's
  state ID as target (`person_show(person_id=...)`) and the zero-argument
  `use<Type>()` hook resolves it ([`react-app-tsx.md`](react-app-tsx.md)).
- **User-scoped** ("my dashboard", "browse all my Persons") → `UI()` on
  `User`.
- **Free-form config the AI fills in** → `request=<Model>` on the UI's
  Type; fields arrive as camelCased props:

```python
class DashboardConfig(Model):
    personalized_message: str = Field(tag=1, default="")


# On `Counter`: the Counter ID stays the implicit target.
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
  // No `id`: resolved from the tool-call target; `undefined` until then.
  const { counter } = useCounter();
  return counter && (
    <CounterValue counter={counter} label={personalizedMessage} />
  );
};
```

`User` creates and locates entities; once the AI holds an ID, that
entity's Readers, Writers and UIs go on its own `Type`.

## Never

- `show_person=UI(request=ShowPersonProps)` on `User`, where
  `ShowPersonProps` carries `person_id: str` — the AI can confuse the ID with
  another entity's, the component must call `usePerson({ id: personId })`
  by hand, and MCPJam shows a leaky entity-ID input. Put
  `show=UI(request=None, path="frontend/mcp/person", ...)` on `Person`;
  entity IDs never go in a `request=<Model>` field.
- A method with no `mcp=` — not even `Workflow`, which is easy to miss;
  codegen rejects it. Write `mcp=None`.
- An application type whose `create` Writer lacks `factory=True` — no
  `create` is generated for the `User` transaction to call.
- `UI(path=...)` without `request=` — no default; write `request=None`.
- `UI(path="mcp/clicker")` or an absolute path — use
  `"frontend/mcp/<name>"`, relative to the project root.
- `mcp=Resource()` — rejected at 1.6.0; use `Tool()`.

## Limits

- `Tool` has only `name` and `title` (1.6.0 `reboot/api.py`); tools carry
  no MCP annotations (`readOnlyHint` etc.), so Claude asks permission
  before every call, Readers included, "Always allow" is per tool, and
  there is no application-side workaround (reboot-crm, 1.6.0).
- `UI()` has no `response=` and no servicer method.

## Scales as

- Each `mcp=Tool()` method adds a tool to the AI's context; hide UI-only
  and human-only methods with `mcp=None`.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `1 validation error for UI` / `request` / `Field required` | `UI()` without `request=` | `request=None` |
| `'Resource()' is not yet supported; use 'Tool()' instead` | `mcp=Resource()` | `mcp=Tool()` |
| `"type[<Type>]" has no attribute "create"` | mypy: the type has no `factory=True` method (observed at 1.4.1) | `factory=True` on its `create` Writer |
| `AttributeError: type object '<Type>' has no attribute '<WrongName>'` | Request/response referenced by source class name | `<Type>.<MethodPascalCase>Request` — see [`api-pydantic.md`](../../python/references/api-pydantic.md) |
| claude.ai shows `Connector not found` for a `UI(request=<Model>)` view after a 200 tool result | The host never requests the view's resource (claude.ai, 2026-10); the same read replayed with the session returns the page | A `UI(request=None)` view renders; diagnose on the host's side, not the server's |

## See also

- [`servicer-patterns.md`](servicer-patterns.md) — implementing the `User` front door
- [`react-app-tsx.md`](react-app-tsx.md) — the UI's zero-arg hook
- [`api-methods.md`](../../python/references/api-methods.md) — factory choice, servicer signatures
