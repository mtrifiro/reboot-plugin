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

The backend calls a model (to summarize, rank, classify, generate,
chat). Backend LLM calls go through `reboot.agents.pydantic_ai.Agent`,
a durable drop-in wrapper over `pydantic_ai.Agent`, run inside a
`Workflow` method. Each model call is memoized with `at_least_once`, so
a workflow replay returns the stored `ModelResponse` instead of
re-hitting and re-billing the provider. Giving the agent tools is
`agent-tools.md`.

## Do this

```python
from reboot.agents.pydantic_ai import Agent
from reboot.aio.contexts import WorkflowContext

# Define the agent once, at module scope — not per request.
# Pydantic AI reads the provider key from the standard env var
# (`ANTHROPIC_API_KEY`); see `lifecycle-secrets.md`.
summarizer = Agent(
    "anthropic:claude-sonnet-4-6",
    name="summarizer",
    system_prompt="You write concise summaries.",
)


@classmethod
async def summarize(cls, context: WorkflowContext) -> None:
    # `context` first, then the prompt. The model call is memoized:
    # a replay returns the cached response, no second API hit.
    result = await summarizer.run(context, "Summarize today's news.")
    summary = result.output
```

To adopt an existing agent: `Agent.wrap(pydantic_ai.Agent(..., name="librarian"))`.
Constructor arguments are `pydantic_ai.Agent`'s, plus the required
`name=`, which scopes every memoization key for the agent's model and
tool calls; it must be unique and stable.

All four entry points take the `WorkflowContext` first (raw
pydantic_ai takes the prompt first):

```python
result = await agent.run(context, "prompt")          # one-shot
async with agent.iter(context, "prompt") as run: ...  # node-by-node
async with agent.run_stream(context, "prompt") as s: ...
async for event in agent.run_stream_events(context, "prompt"): ...
```

An on-demand "do it now" method (an MCP tool, a button) is a
`Writer`/`Transaction` that only schedules the workflow
(`await self.ref().schedule().summarize(context)`), never one that
makes the model call itself.

Within one workflow method, or one `context.loop` iteration, every run
must be distinguishable by `(user_prompt, variant, message_history)`.
Repeat a prompt with a distinct `variant=`:

```python
first = await agent.run(context, "Draft a title.")
second = await agent.run(context, "Draft a title.", variant="retry")
```

Identical runs in different loop iterations are fine; each iteration
is a fresh scope.

### Dependency

Add the `anthropic` extra to the `reboot` requirement, keeping the pin
(`lifecycle-project-setup.md`):

```toml
dependencies = [
    "reboot[anthropic]==1.6.0",
]
```

`reboot` already pins `pydantic-ai-slim`; the extra adds the Anthropic
SDK at a version that works with it.

## Never

- `anthropic.Anthropic().messages.create(...)` or a bare
  `pydantic_ai.Agent` in a workflow — it runs again on every replay,
  re-bills, and returns a different answer, breaking deterministic
  replay.
- A model call in a `Transaction` or `Writer` — Reboot retries
  transactions, so one logical request is billed several times, and
  nothing memoizes it. The `Agent` refuses any non-workflow context.
- `agent.run("prompt")` (prompt first) — raises `UserError` naming the
  fix.
- `run_sync` / `run_stream_sync` — raise; Reboot is async-only.
- Starting an agent run from inside another (e.g. from a tool) —
  nested runs raise `UserError`.
- Setting `agent.name` after construction — raises; it would shift
  every memoization key. Construct a new `Agent` to rename.
- `parallel_execution_mode="parallel"` (pydantic_ai's default) —
  rejected at construction; its completion-order events differ across
  replays. The Reboot default `"parallel_ordered_events"` and
  `"sequential"` are the accepted values.
- Adding `pydantic-ai-slim[anthropic]` or `anthropic` to
  `pyproject.toml` yourself — a fresh resolve picks an SDK built on
  `httpx2`, which rejects the `httpx` client Pydantic AI hands it.
- Tool functions or `output_type` classes defined as local closures and
  passed per run — they must pickle; define them at module scope.

## Limits

- Runs only in a `WorkflowContext`; unusable from readers, writers and
  transactions.
- Streaming is drained, not token-by-token: `run_stream`,
  `run_stream_events` and `iter` work, but the model call is drained
  and memoized inside `at_least_once`, so chunks arrive in one batch
  when the model finishes. A chat UI shows nothing until then (~30–60 s
  for a long document, mattprd at 1.4.1); there is no sanctioned
  side channel for partial output at 1.6.0.
- Model calls pass `effect_validation=EffectValidation.DISABLED`
  (1.6.0 source), so development and the test harness do not call the
  provider twice. Tool calls do not opt out (`agent-tools.md`). The
  no-re-billing promise above covers replay plus this opt-out, not
  every call your workflow makes around the agent.
- On replay the agent compares its configuration snapshot
  (instructions, model, per-run kwargs) with the original run and logs
  `*** POSSIBLE NON-DETERMINISM! ***` if anything changed; memoized
  responses may then be stale.
- Per-run `toolsets=` / `output_type=` must be picklable.

## Scales as

- One provider call per model step on first execution; zero on replay
  (memoized). Tool-using runs make one model call per step plus tool
  calls (framework design).

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
