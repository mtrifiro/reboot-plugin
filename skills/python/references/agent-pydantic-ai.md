---
title: Call LLMs via the Reboot `Agent`, Never a Raw SDK
impact: HIGH
impactDescription: A raw LLM call re-hits the provider on every workflow replay — wasteful, non-deterministic, double-billed
tags: agent, llm, pydantic-ai, workflow, memoize, durable
summary: "Never call a raw LLM SDK or put a model call in a writer/transaction; use `reboot.agents.pydantic_ai.Agent` with a stable `name=` inside a `Workflow`, `variant=` for repeats; streaming is drained."
step: servicer
applies: [mcp-ui, web-app, backend-only]
always: false
when: "the backend calls an LLM"
verified: 1.6.0
docs: ""
---

# Call LLMs via the Reboot `Agent`, Never a Raw SDK

## When you are here

The backend calls a model (summarize, rank, classify, generate, chat).
Use `reboot.agents.pydantic_ai.Agent`, a durable drop-in wrapper over
`pydantic_ai.Agent`, inside a `Workflow` method: each model call is
memoized with `at_least_once`, so replay returns the stored
`ModelResponse` instead of re-billing the provider. Tools:
`agent-tools.md`.

## Do this

```python
from reboot.agents.pydantic_ai import Agent
from reboot.aio.contexts import WorkflowContext

# Once, at module scope. Key from `ANTHROPIC_API_KEY` (`lifecycle-secrets.md`).
summarizer = Agent(
    "anthropic:claude-sonnet-4-6",
    name="summarizer",
    system_prompt="You write concise summaries.",
)


@classmethod
async def summarize(cls, context: WorkflowContext) -> None:
    # `context` first, then the prompt; replay returns the cached response.
    result = await summarizer.run(context, "Summarize today's news.")
    summary = result.output
```

- Constructor arguments are `pydantic_ai.Agent`'s plus the required
  `name=`, which scopes every memo key for its model and tool calls;
  unique and stable. Adopt an existing agent with
  `Agent.wrap(pydantic_ai.Agent(..., name="librarian"))`.
- All four entry points take `WorkflowContext` first (raw pydantic_ai
  takes the prompt first):

```python
result = await agent.run(context, "prompt")          # one-shot
async with agent.iter(context, "prompt") as run: ...  # node-by-node
async with agent.run_stream(context, "prompt") as s: ...
async for event in agent.run_stream_events(context, "prompt"): ...
```

- An on-demand method (an MCP tool, a button) is a `Writer`/`Transaction`
  that only schedules the workflow
  (`await self.ref().schedule().summarize(context)`), never one that
  calls the model.
- Within one workflow method or `context.loop` iteration, runs must
  differ by `(user_prompt, variant, message_history)`; repeat a prompt
  with a distinct `variant=`:
  `second = await agent.run(context, "Draft a title.", variant="retry")`.
  Identical runs in different iterations are fine.

### Dependency

Add the `anthropic` extra to `reboot`, keeping the pin
(`lifecycle-project-setup.md`); `reboot` already pins
`pydantic-ai-slim` and the extra adds a compatible Anthropic SDK:

```toml
dependencies = [
    "reboot[anthropic]==1.6.0",
]
```

## Never

- `anthropic.Anthropic().messages.create(...)` or a bare
  `pydantic_ai.Agent` in a workflow — re-runs on every replay,
  re-bills, and answers differently, breaking deterministic replay.
- A model call in a `Transaction` or `Writer` — transactions are
  retried, so one request bills several times, unmemoized. The `Agent`
  refuses non-workflow contexts.
- `agent.run("prompt")` (prompt first) — raises `UserError` naming the
  fix.
- `run_sync` / `run_stream_sync` — raise; Reboot is async-only.
- Starting an agent run from inside another (e.g. from a tool) —
  raises `UserError`.
- Setting `agent.name` after construction — raises (it would shift
  every memo key); construct a new `Agent`.
- `parallel_execution_mode="parallel"` (pydantic_ai's default) —
  rejected at construction; completion-order events differ across
  replays. Accepted: the Reboot default `"parallel_ordered_events"`, or
  `"sequential"`.
- Adding `pydantic-ai-slim[anthropic]` or `anthropic` to
  `pyproject.toml` yourself — a fresh resolve picks an SDK built on
  `httpx2`, which rejects the `httpx` client Pydantic AI passes.
- Tool functions or `output_type` classes defined as local closures and
  passed per run — they must pickle; define them at module scope.

## Limits

- `WorkflowContext` only; unusable from readers, writers, transactions.
- Streaming is drained, not token-by-token: `run_stream`,
  `run_stream_events` and `iter` work, but the model call is drained and
  memoized inside `at_least_once`, so chunks arrive in one batch at the
  end. A chat UI shows nothing until then (~30–60 s for a long document,
  mattprd at 1.4.1); no sanctioned side channel for partial output at
  1.6.0.
- Model calls pass `effect_validation=EffectValidation.DISABLED` (1.6.0
  source), so dev and tests don't call the provider twice; tool calls do
  not opt out (`agent-tools.md`). The no-re-billing promise covers
  replay plus this opt-out, not other calls around the agent.
- On replay the agent compares its configuration snapshot
  (instructions, model, per-run kwargs) with the original and logs
  `*** POSSIBLE NON-DETERMINISM! ***` on a change; memoized responses
  may then be stale.
- Per-run `toolsets=` / `output_type=` must be picklable.

## Scales as

- One provider call per model step on first execution, zero on replay;
  tool-using runs add their tool calls (framework design).

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `` `Agent.run` requires `context: WorkflowContext` as its first positional argument `` | Called from a non-workflow context, or prompt passed first | Move the call into a `Workflow`; pass `context` first |
| `` An agent needs to have a unique `name` in order to be used with Reboot `` | Constructed without `name=` | Add a stable `name=` |
| `Duplicate agent run:` | Two indistinguishable runs in one method / iteration | Pass a distinct `variant=` |
| `Nested agent runs are not supported` | A run started inside another | Restructure; call sequentially |
| `` `Agent.run_sync` is not supported `` | Sync entry point | `await agent.run(context, ...)` |
| `` `parallel_execution_mode='parallel'` is not supported on a Reboot `Agent` `` | pydantic_ai default mode | Omit it, or `"sequential"` |
| ``Invalid `http_client` argument`` | Hand-added `anthropic` resolved an `httpx2` SDK | Use `reboot[anthropic]==1.6.0` only |

## See also

- [`agent-tools.md`](agent-tools.md) — tools that read and mutate state
- [`servicer-workflow-external.md`](servicer-workflow-external.md) — `at_least_once` and effect validation
- [`servicer-workflow-declare.md`](servicer-workflow-declare.md) — declaring and scheduling the workflow
