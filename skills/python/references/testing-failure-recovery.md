---
title: Test Failure Recovery — `rbt.down()` and `rbt.up(revision=...)`
impact: MEDIUM
impactDescription: Durability is the reason to build on Reboot; a suite that never restarts the app never tests it
tags: testing, recovery, restart, down, up, revision, crash, effect-validation, exactly-once, mocking, tasks, workflows, idempotency
summary: "Restart mid-flight with `rbt.down()` / `rbt.up(revision=...)`, land the crash with a stalling mock, assert in-flight work happened exactly once; don't test that committed data survives."
step: tests
applies: [mcp-ui, web-app, backend-only]
always: false
when: "the app has a spawned task, a `Workflow`, or scheduled work"
verified: 1.6.0
docs: ""
---

# Test Failure Recovery — `rbt.down()` and `rbt.up(revision=...)`

## When you are here

The app has a spawned task, a `Workflow` or scheduled work, and you
want to prove it survives a crash: the harness takes the app down
mid-flight and brings it back. This is the one test that stays on the
harness rather than in a feature file ([`testing-features.md`](testing-features.md));
harness basics: [`testing-harness.md`](testing-harness.md).

## Do this

Test what was **in flight** when the process died (a task half-run, a
workflow between steps, an effect that must land exactly once) and the
invariants partial recovery could break (no double-count, no second
payment).

### The restart primitive

`up()` returns an `ApplicationRevision`; pass it back to bring the
*same* application up again:

```python
revision = await self.rbt.up(Application(servicers=[OrderServicer]))
# ... calls ...
await self.rbt.down()                    # the process dies
await self.rbt.up(revision=revision)     # ...and comes back
```

Restarting an idle app proves little. A second `up()` may register a
*different* `Application(...)` to test an upgrade across a restart
([`api-schema-evolution.md`](api-schema-evolution.md)).
`asyncTearDown` stays `await self.rbt.stop()`: `down()` stops the
servers, `stop()` tears down the harness.

### Put the crash exactly where you want it

Patch the method under test (at its **import location in the consuming
module**) with one that blocks until the app is down. `reached_mark_paid`
proves the app is inside the method before the kill; `app_is_down`
releases it only after. A servicer subclass overriding the method also
works, and reads better when several tests share the stall.

```python
import asyncio
from unittest import mock


async def test_fulfillment_survives_a_crash_mid_flight(self) -> None:
    reached_mark_paid = asyncio.Event()
    app_is_down = asyncio.Event()

    # `mark_paid` is the writer the `fulfill` workflow calls once paid.
    original_mark_paid = OrderServicer.mark_paid

    async def stalling_mark_paid(self, context, request):
        reached_mark_paid.set()
        await app_is_down.wait()  # crash lands inside `mark_paid`
        return await original_mark_paid(self, context, request)

    with mock.patch(
        "servicers.orders.OrderServicer.mark_paid",
        stalling_mark_paid,
    ):
        revision = await self.rbt.up(
            Application(servicers=[OrderServicer]),
        )
        context = self.rbt.create_external_context(
            name=f"test-{self.id()}"
        )

        order = Order.ref(f"order-{self.id()}")
        await order.place(context, sku="ABC", quantity=2)
        task = await order.spawn().fulfill(context)

        await reached_mark_paid.wait()

        await self.rbt.down()
        app_is_down.set()

        await self.rbt.up(revision=revision)

        await task  # the workflow resumed and completed

    # Assert the invariant the app promises, not that data survived.
    response = await order.get(context)
    self.assertEqual(response.status, "fulfilled")
    self.assertEqual(len(response.payments), 1)
```

### Counting calls: disable effect validation

The harness enables effect validation by default: it aborts the first
run of every writer and transaction body and runs it again (only the
second commits; runs are not compared), to surface bodies unsafe to
re-execute ([`servicer-writer.md`](servicer-writer.md)). A `nonlocal`
counter therefore over-reports. A test that counts invocations turns
it off:

```python
from reboot.aio.contexts import EffectValidation

revision = await self.rbt.up(
    Application(servicers=[OrderServicer]),
    effect_validation=EffectValidation.DISABLED,
)
```

For one external call in a workflow it is per call:
`at_least_once(..., effect_validation=EffectValidation.DISABLED)`;
otherwise the callable runs twice and the **second** result is memoized.

### What's worth a recovery test

- **A spawned task** — cancelled at `down()`, picked up on `up()`;
  assert it completes and its effect happened once.
- **A `Workflow`** — its body replays from the top; assert finished
  steps did not repeat: writer/transaction calls under
  `.per_workflow(...)` / `.per_iteration(...)`, and any
  `at_least_once` / `at_most_once` call.
- **`schedule()`d work** — still fires after a restart spanning its due time.
- **A half-finished multi-actor transaction** — fully applied or fully
  rolled back, never half.

## Never

- **A test that "the data is still there" after a restart** —
  that re-tests Reboot's guarantee, not the app.
- **`revision=` together with `application=` / `servicers=`** — the
  revision already carries the configuration; pass it alone.
- **A second `up()` without `down()`** — refused while the app is up.
- **Awaiting a unary call from the test's context while the app is
  down** — an `ExternalContext` retries `Unavailable` without limit, so
  it waits instead of failing; `up()` before the next call.
- **A stand-in for an external call that answers from a counter** —
  under effect validation `at_least_once` keeps the second answer.
  Derive the answer from the input.
- **Overriding `authorizer()` in a stalling subclass** — mock behavior
  only.

## Limits

- Calls *inside* the app are not retried per call; a `Workflow`
  re-runs its body, and every memoizing primitive (`at_least_once`,
  `at_most_once`, `until`, `until_changes`, Reboot calls scoped
  `.per_workflow(...)` / `.per_iteration(...)`) returns its recorded
  result on replay.
- `effect_validation=` cannot be passed with `revision=`; the
  revision keeps the first `up()`'s setting (1.6.0 source).
- Two transactions on one actor racing (a confirm against its hold's
  expiry timer) starved each other at the 30 s lock deadline with
  validation on, and proceeded with it off (theater-network, 1.4.0).

## Scales as

- Effect validation roughly doubles the cost of mutation-heavy tests
  ([`testing-harness.md`](testing-harness.md)).

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `This application is already up; ` | `up()` called twice with no `down()` | `await self.rbt.down()` first |
| `Only one of 'application' OR 'revision' can be passed` | `application=` alongside `revision=` | Pass `revision=` alone |
| `Not expecting 'servers'` / `Not expecting 'effect_validation'` | Passed alongside `revision=` | Pass `revision=` alone |

## See also

- [`testing-harness.md`](testing-harness.md) — `Reboot()`, `up()`, effect validation default
- [`servicer-workflow-calls.md`](servicer-workflow-calls.md) — what replays and what reruns
- [`testing-external-context.md`](testing-external-context.md) — mocking by import location
