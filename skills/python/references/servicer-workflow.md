---
title: Building Durable Workflows
impact: CRITICAL
impactDescription: Router for the six workflow parts; the wrong shape breaks replay, and the wrong call primitive double-charges users, poisons workflows forever, or stalls progress
tags: workflow, WorkflowContext, classmethod, durable, replay, at_least_once, at_most_once, per_workflow, per_iteration, always, loop, until, until_changes, spawn
summary: "Router to six workflow parts (declare, Reboot calls, external calls, `context.loop`, waiting, exit) and when to read each."
step: servicer
applies: [mcp-ui, web-app, backend-only]
always: false
when: "you declared a `Workflow`"
verified: 1.6.0
docs: ""
---

# Building Durable Workflows

## When you are here

You declared a `Workflow(...)` method: a durable function on an actor
whose body may re-execute on replay while memoized steps return cached
results. Read each part below when you reach its moment.

## Do this

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
- A plain `await` on anything with effects — every `await` takes the
  primitive for what it calls (calls part).
- `schedule(...)` from a workflow — use `spawn(...)` (declare part).
- A wall-clock or random value read directly in the body — capture it
  with `at_least_once` (external part).
- Driving the phase after a commit from a plan rebuilt locally — after
  an unclean kill a workflow replayed onto a different path and wedged
  (agentic-demo, 1.4.0). Drive post-commit phases from the actor's
  committed state.

## Limits

- Stopping the app pauses workflows; they resume on the next start.
- Effect validation in development re-runs memoized `at_least_once`
  callables and the last loop iteration, and can re-submit a completed
  `per_workflow` transaction against state the first run already
  changed (agentic-demo, 1.4.0): make terminal handling idempotent
  (already resolved by me is success; never demote a terminal state;
  gate narrative events on what the workflow observed).

## Scales as

- Not measured.

## Errors you will see

None known. Each part lists its own.

## See also

- [`api-methods.md`](api-methods.md) — the `Workflow(...)` factory and servicer signature
- [`agent-pydantic-ai.md`](agent-pydantic-ai.md) — LLM calls inside a workflow
- [`scheduling-recurring.md`](scheduling-recurring.md) — recurring jobs dispatching workflows
