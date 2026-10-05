---
title: Give the Agent Tools with `@agent.tool` and `@agent.tool_plain`
impact: HIGH
impactDescription: Tools are how an LLM agent reads and mutates Reboot state; the wrong signature won't receive the `WorkflowContext`
tags: agent, llm, tools, pydantic-ai, workflow
summary: "Tools need `WorkflowContext` first, `RunContext` second, or miss Reboot state; they run twice under effect validation; `@agent.tool_plain`."
step: servicer
applies: [mcp-ui, web-app, backend-only]
always: false
when: "an LLM agent needs tools that read or change Reboot state"
verified: 1.6.0
docs: ""
---

# Give the Agent Tools with `@agent.tool` and `@agent.tool_plain`

## When you are here

The model needs to read or change application state during a Reboot
`Agent` run (`agent-pydantic-ai.md`). Register tools as on
`pydantic_ai.Agent`, except an `@agent.tool` function takes the durable
`WorkflowContext` first; that is how it reaches Reboot actors.

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
    state = await Page.ref(page_id).get(context)
    return {"title": state.title, "content": state.content}


@agent.tool_plain
async def add(x: int, y: int) -> int:
    # No Reboot actors, no agent deps: `tool_plain`.
    return x + y
```

- Agent deps come from `run.deps`. Both decorators accept the
  parametrized form (`@agent.tool(retries=2)`).
- At construction, `tools=` takes plain tool functions and `toolsets=`
  pydantic_ai toolsets (including `MCPServer` instances):
  `Agent("anthropic:claude-sonnet-4-6", name="librarian", tools=[some_tool], toolsets=[some_function_toolset])`.
- Tools decorated after `Agent.wrap(...)` are picked up too.

## Never

- `async def get_page(run: RunContext[Deps], page_id: str)` under
  `@agent.tool` — no `WorkflowContext`, so it cannot call
  `Page.ref(...)`. Put `context: WorkflowContext` first, `RunContext`
  second.
- A tool body that is unsafe to run twice (charges a card, sends an
  email, appends without a key) — in development and tests it does run
  twice (see Limits).
- Per-run `toolsets=` built from local closures — they cannot pickle
  and raise `UserError`; define tool functions at module scope.
- Returning a value that cannot be pickled — the memoized result is
  pickled.

## Limits

- Every tool call runs inside `at_least_once` (alias
  `"Tool call for step #<n>"`): on replay a completed tool returns its
  cached result.
- Unlike model calls, tool calls keep effect validation on (1.6.0
  source): under `rbt dev run` and tests the body runs twice and the
  second result is memoized, with no per-call opt-out. Keep tools
  idempotent, or move expensive/side-effecting work into its own
  workflow step (rule: `servicer-workflow-external.md`).

## Scales as

- Not measured. Each tool call is one memoized step costing whatever
  its body does (twice in development).

## Errors you will see

None known.

## See also

- [`agent-pydantic-ai.md`](agent-pydantic-ai.md) — constructing and running the `Agent`
- [`rpc-calls.md`](rpc-calls.md) — calling actor methods inside a tool
- [`servicer-workflow-external.md`](servicer-workflow-external.md) — `at_least_once` and effect validation
