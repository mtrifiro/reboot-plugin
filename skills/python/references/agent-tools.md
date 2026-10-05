---
title: Give the Agent Tools with `@agent.tool` and `@agent.tool_plain`
impact: HIGH
impactDescription: Tools are how an LLM agent reads and mutates Reboot state; the wrong signature won't receive the `WorkflowContext`
tags: agent, llm, tools, pydantic-ai, workflow
summary: "Tools take `WorkflowContext` first and `RunContext` second, or they never see Reboot state; `@agent.tool_plain` for state-free tools; tool calls are memoized but run twice under effect validation."
step: servicer
applies: [mcp-ui, web-app, backend-only]
always: false
when: "an LLM agent needs tools that read or change Reboot state"
verified: 1.6.0
docs: ""
---

# Give the Agent Tools with `@agent.tool` and `@agent.tool_plain`

## When you are here

You have a Reboot `Agent` (`agent-pydantic-ai.md`) and the model needs
to read or change application state during a run. Register tools as on
a `pydantic_ai.Agent`, except that an `@agent.tool` function receives
the durable `WorkflowContext` as its first parameter. That context is
how a tool reaches Reboot actors.

## Do this

```python
from pydantic_ai import RunContext
from reboot.agents.pydantic_ai import Agent
from reboot.aio.contexts import WorkflowContext

agent = Agent("anthropic:claude-sonnet-4-6", name="librarian")


@agent.tool
async def get_page(
    context: WorkflowContext,
    run: RunContext[Deps],
    page_id: str,
) -> dict:
    """Read a page's title and content."""
    # The `WorkflowContext` reaches Reboot actors through the same
    # durable envelope as the rest of the workflow.
    state = await Page.ref(page_id).get(context)
    return {"title": state.title, "content": state.content}


@agent.tool_plain
async def add(x: int, y: int) -> int:
    # No Reboot actors, no agent deps: `tool_plain`.
    return x + y
```

Both decorators accept the parametrized form (`@agent.tool(retries=2)`).
Agent deps come from `run.deps`.

Tools can also be passed at construction: `tools=` takes plain tool
functions, `toolsets=` takes pydantic_ai toolsets (including
`MCPServer` instances):

```python
agent = Agent(
    "anthropic:claude-sonnet-4-6",
    name="librarian",
    tools=[some_tool],
    toolsets=[some_function_toolset],
)
```

Tools added with `@agent.tool` / `@agent.tool_plain` after
`Agent.wrap(...)` are picked up too; no need to register them on the
wrapped agent.

## Never

- `async def get_page(run: RunContext[Deps], page_id: str)` under
  `@agent.tool` — the raw pydantic_ai signature has no
  `WorkflowContext`, so the tool cannot call `Page.ref(...)`. Put
  `context: WorkflowContext` first, `RunContext` second.
- A tool body that is unsafe to run twice (charges a card, sends an
  email, appends without a key) — in development and the test harness
  it does run twice; see Limits.
- Per-run `toolsets=` built from local closures — they cannot pickle
  and raise `UserError`; define tool functions at module scope.
- Returning a value that cannot be pickled — the memoized result is
  pickled.

## Limits

- Every tool call runs inside `at_least_once` (alias
  `"Tool call for step #<n>"`), so on a workflow replay a completed
  tool returns its cached result without running the body.
- That covers replay, not effect validation. Unlike the agent's model
  calls, tool calls keep effect validation on (1.6.0 source): under
  `rbt dev run` and the test harness the body runs twice and the second
  result is memoized. The tool has no per-call opt-out; keep it
  idempotent, or make the expensive or side-effecting work its own
  workflow step outside the tool. The effect-validation rule itself is
  in `servicer-workflow-external.md`.

## Scales as

- Not measured. Each tool call is one memoized step; its first
  execution costs whatever the body does (twice in development).

## Errors you will see

None known.

## See also

- [`agent-pydantic-ai.md`](agent-pydantic-ai.md) — constructing and running the `Agent`
- [`rpc-calls.md`](rpc-calls.md) — calling actor methods inside a tool
- [`servicer-workflow-external.md`](servicer-workflow-external.md) — `at_least_once` and effect validation
