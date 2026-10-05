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
want to prove it survives a crash. The harness can take the application
down mid-flight and bring it back, which turns "survives a crash" into
an ordinary assertion. This is the one kind of test that stays on the
harness instead of in a feature file
([`testing-features.md`](testing-features.md)); the harness itself is
[`testing-harness.md`](testing-harness.md).

## Do this

Test what the app had **in flight** when the process died (a task
half-run, a workflow between steps, an effect that must land exactly
once) and the invariants a partial recovery could break (a counter
that must not double-count, a payment that must not go out twice).

### The restart primitive

`up()` returns an `ApplicationRevision`; pass it back to bring the
*same* application up again:

```python
revision = await self.rbt.up(Application(servicers=[OrderServicer]))

context = self.rbt.create_external_context(name=f"test-{self.id()}")
order = Order.ref(f"order-{self.id()}")
await order.place(context, sku="ABC", quantity=2)

# The process dies.
await self.rbt.down()

# ...and comes back.
await self.rbt.up(revision=revision)
```

That restarts an idle application, which recovers trivially. A second
`up()` may instead register a *different* `Application(...)`, which is
how a test exercises an upgrade across a restart
([`api-schema-evolution.md`](api-schema-evolution.md)).
`asyncTearDown` stays `await self.rbt.stop()`: `down()` stops the
servers, `stop()` tears down the harness.

### Put the crash exactly where you want it

Patch the method under test with one that blocks until the test has
taken the app down:

```python
import asyncio
from unittest import mock


async def test_fulfillment_survives_a_crash_mid_flight(self) -> None:
    reached_mark_paid = asyncio.Event()
    app_is_down = asyncio.Event()

    # `mark_paid` is the writer the `fulfill` workflow calls once the
    # payment goes through.
    original_mark_paid = OrderServicer.mark_paid

    async def stalling_mark_paid(self, context, request):
        reached_mark_paid.set()
        # Hold the method open until the test kills the app, so the
        # crash lands inside `mark_paid` rather than between calls.
        await app_is_down.wait()
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

        # Wait until the app is provably inside `mark_paid`.
        await reached_mark_paid.wait()

        await self.rbt.down()
        app_is_down.set()

        await self.rbt.up(revision=revision)

        # The workflow was picked back up and ran to completion.
        await task

    # The payment was recorded exactly once, despite the crash.
    response = await order.get(context)
    self.assertEqual(response.status, "fulfilled")
    self.assertEqual(len(response.payments), 1)
```

The two events make it deterministic: `reached_mark_paid` proves the
app got into the method before the kill, `app_is_down` releases it only
after. Patch by the **import location in the consuming module**.
Subclassing the servicer and overriding the method works too, and
reads better when several tests share the stall.

### Assert state, not call counts

```python
# GOOD — the invariant the app actually promises.
response = await order.get(context)
self.assertEqual(len(response.payments), 1)

# WEAK — this only re-tests Reboot's durability guarantee.
self.assertEqual(response.quantity, 2)
```

If a test does count invocations of a writer or transaction body, turn
effect validation off for that test. In unit tests the harness enables
it by default: it deliberately aborts the first run of every writer and
transaction body and runs it again (only the second run commits; the
runs are not compared), to surface bodies that aren't safe to
re-execute (see [`servicer-writer.md`](servicer-writer.md)). A
`nonlocal` counter therefore reports more calls than the test made:

```python
from reboot.aio.contexts import EffectValidation

revision = await self.rbt.up(
    Application(servicers=[OrderServicer]),
    # This test counts calls with a `nonlocal`, which effect
    # validation's deliberate re-execution would inflate.
    effect_validation=EffectValidation.DISABLED,
)
```

For one external call inside a workflow, the switch is per call:
`at_least_once(..., effect_validation=EffectValidation.DISABLED)`.
Without it the callable runs twice and the **second** result is
memoized.

### What's worth a recovery test

- **A spawned task** — cancelled when the app goes down, picked up on
  `up()`; assert it completes and its effect happened once.
- **A `Workflow`** — its body re-executes from the top on replay;
  assert the steps already finished did not happen twice: writer and
  transaction calls under `.per_workflow(...)` / `.per_iteration(...)`,
  and any `at_least_once` / `at_most_once` call.
- **`schedule()`d work** — assert it still fires after a restart that
  spans its due time.
- **A half-finished multi-actor transaction** — fully applied or fully
  rolled back, never half.

## Never

- **A test that "the data is still there" after a restart** —
  committed state surviving is Reboot's guarantee, covered by its own
  suite; re-asserting it checks Reboot, not the app.
- **`revision=` together with `application=` / `servicers=`** — the
  revision already carries the configuration; pass it alone.
- **A second `up()` without `down()`** — refused while the app is up.
- **Awaiting a unary call from the test's context while the app is
  down** — an `ExternalContext` retries `Unavailable` with no attempt
  limit, so the call waits for the app instead of failing. Assert
  what you can offline, then `up()` before the next call.
- **A stand-in for an external call that answers from a counter** —
  under effect validation `at_least_once` keeps the second answer.
  Derive the answer from the input.
- **Overriding `authorizer()` in a stalling subclass** — mock behavior
  only.

## Limits

- Calls made *inside* the app are not retried per call. A `Workflow`
  recovers by re-running its body from the top; every memoizing
  primitive (`at_least_once`, `at_most_once`, `until`,
  `until_changes`, and Reboot calls scoped `.per_workflow(...)` /
  `.per_iteration(...)`) returns its recorded result on replay instead
  of redoing the work.
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
