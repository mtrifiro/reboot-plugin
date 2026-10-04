---
title: Building Durable Workflows
impact: CRITICAL
impactDescription: Router for the six workflow parts; the wrong shape breaks replay, and the wrong call primitive double-charges users, poisons workflows forever, or stalls progress
tags: workflow, WorkflowContext, classmethod, durable, replay, at_least_once, at_most_once, per_workflow, per_iteration, always, loop, until, until_changes, spawn
step: servicer
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: ""
---

# Building Durable Workflows

## When you are here

You declared a `Workflow(...)` method. A workflow is a durable function
attached to an actor: its body may re-execute on replay, and memoized
steps return their cached results. This file routes you to the part you
need at each moment; read each part when you reach that moment.

## Do this

Read in build order:

| Part | Read it when |
| --- | --- |
| [`servicer-workflow-declare.md`](servicer-workflow-declare.md) | Writing the servicer method, or starting the workflow from somewhere else |
| [`servicer-workflow-calls.md`](servicer-workflow-calls.md) | About to `await` anything in the body; calling Reboot actors or writing this actor's state |
| [`servicer-workflow-external.md`](servicer-workflow-external.md) | Calling HTTP, payments, SMS, the clock or randomness; LLM calls start here |
| [`servicer-workflow-loop.md`](servicer-workflow-loop.md) | The body should repeat |
| [`servicer-workflow-wait.md`](servicer-workflow-wait.md) | Blocking until Reboot state changes, or waiting on external work |
| [`servicer-workflow-exit.md`](servicer-workflow-exit.md) | Deciding how the workflow stops on failure |

## Never

- `self` or `self.state` in a workflow — it is a `@classmethod`.
- A plain `await` on anything with effects — every `await` takes a
  primitive chosen by what it calls (calls part).
- `schedule(...)` from a workflow — use `spawn(...)` (declare part).
- A wall-clock or random value read directly in the body — capture it
  with `at_least_once` (external part).

## Limits

- Stopping the app pauses workflows; they resume on the next start.
- Effect validation in development re-runs memoized `at_least_once`
  callables and the last loop iteration.

## Scales as

- Not measured.

## Errors you will see

None known. Each part lists its own.

## See also

- [`api-methods.md`](api-methods.md) — the `Workflow(...)` factory and servicer signature
- [`agent-pydantic-ai.md`](agent-pydantic-ai.md) — LLM calls inside a workflow
- [`scheduling-recurring.md`](scheduling-recurring.md) — recurring jobs dispatching workflows
