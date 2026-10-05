---
title: Drive Tests with `create_external_context`, Assert, Wait, and Mock
impact: MEDIUM
impactDescription: Tests can't call into the application, observe errors, or wait for workflows without these patterns
tags: testing, external-context, RPC, harness, aborted, errors, mocking, workflows, user-stories, idempotency
summary: "`create_external_context` with a unique name per test; asserting `<Method>Aborted`, live updates with `reactively()`, waiting on spawned tasks and workflows, mocking external services and LLMs."
step: tests
applies: [mcp-ui, web-app, backend-only]
always: false
when: "writing custom steps or harness tests"
verified: 1.6.0
docs: ""
---

# Drive Tests with `create_external_context`, Assert, Wait, and Mock

## When you are here

You are writing Python that calls the application from a test: a
custom step body, or an `IsolatedAsyncioTestCase` on the `Reboot()`
harness. A user-observable behavior belongs in a feature file
([`testing-features.md`](testing-features.md)); the harness setup
(`self.rbt`, `up()`, impersonation) is
[`testing-harness.md`](testing-harness.md).

## Do this

A test calls the app through a context from
`rbt.create_external_context(name=...)`, passed as `context` to actor
method calls. It plays an outside caller, can call any method
(transactions included), and can drive many calls:

```python
async def test_chat_room(self) -> None:
    await self.rbt.up(Application(servicers=[ChatRoomServicer]))

    context = self.rbt.create_external_context(name=f"test-{self.id()}")
    chat_room = ChatRoom.ref("testing-chat-room")

    await chat_room.send(context, message="Hello, World")
    await chat_room.send(context, message="Hello, Reboot!")

    response = await chat_room.messages(context)
    self.assertEqual(response.messages, ["Hello, World", "Hello, Reboot!"])
```

Name the context after the test (`f"test-{self.id()}"`) so a failing
test's trace is identifiable. To satisfy real authorizers, call as a
user: `await self.rbt.create_external_context_as(name, user_id)` (after
`up()`). A second user is a second context:

```python
other_context = await self.rbt.create_external_context_as(
    name=f"other-{self.id()}",
    user_id="other-user",
)
with self.assertRaises(Aborted):
    await Cart.ref(cart.state_id).get_cart(other_context)
```

### Asserting an abort

A declared error surfaces as the generated `<Service>.<Method>Aborted`,
whose `.error` is the error model:

```python
with self.assertRaises(Cart.CheckoutAborted) as cm:
    await cart.checkout(
        self.context,
        shipping_address=SHIPPING,
        coupon_code="definitely-not-a-real-code",
    )
self.assertIsInstance(cm.exception.error, InvalidCoupon)
```

`try` / `except Account.WithdrawAborted as aborted:` with
`isinstance(aborted.error, OverdraftError)` is equivalent. When you only
care that the call failed (a denial), assert
`reboot.aio.aborted.Aborted`.

### Asserting a live update: `reactively()`

`Type.ref(id).reactively().<reader>(context)` is an async iterator that
yields a fresh response on every state change, the subscription the
React hooks use:

```python
subscription = TaskList.ref(list_id).reactively().get(bob)
first = await asyncio.wait_for(anext(subscription), timeout=10)
self.assertEqual(first.tasks, [])

await TaskList.ref(list_id).add_task(alice, title="Milk")

while True:
    update = await asyncio.wait_for(anext(subscription), timeout=10)
    if len(update.tasks) == 1:
        break
self.assertEqual(update.tasks[0].title, "Milk")
```

Wrap every `anext()` in `asyncio.wait_for` so a missing update fails
fast, and loop until the expected state: an intermediate snapshot may
arrive first.

### Waiting for spawned tasks

A method that spawns a task returns a `task_id` at once; wait with
`<Service>.<Task>.retrieve`:

```python
hello_servicer.SECS_UNTIL_WARNING = 0
hello_servicer.ADDITIONAL_SECS_UNTIL_ERASE = 0

send_response = await hello.send(context, message="Hello, World!")
warning_response = await Hello.WarningTask.retrieve(
    context,
    task_id=send_response.task_id,
)
await Hello.EraseTask.retrieve(context, task_id=warning_response.task_id)

messages_response = await hello.messages(context)
self.assertEqual(len(messages_response.messages), 1)
```

For a workflow driven by a mocked external service, an
`asyncio.Event` the mock sets at its terminal step is the sync point.

### Mocking externals

**1. Override a method on a Servicer subclass**, and register the
subclass in place of the original:

```python
class NoFulfillOrderServicer(OrderServicer):
    """Skip the Printful call during tests."""

    @classmethod
    async def fulfill(
        cls,
        context: WorkflowContext,
        request: Order.FulfillRequest,
    ) -> None:
        return None
```

**2. `unittest.mock.patch` a plain helper**, at its import location in
the consuming module:

```python
with patch(
    "servicers.store.fetch_products",
    new=AsyncMock(return_value=catalog),
):
    response = await User.ref(self.user_id).list_products(self.context)
```

**3. A scripted `FunctionModel` for a pydantic-AI agent**:

```python
import asyncio
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart


class ScriptedAgent:
    def __init__(self) -> None:
        self.done = asyncio.Event()

    async def step(self, messages, info: AgentInfo) -> ModelResponse:
        # Inspect tool-returns in `messages`, pick the next
        # `ToolCallPart` to emit, and `self.done.set()` on the
        # terminal response.
        ...


# In asyncSetUp. `wrapped` is typed `AbstractAgent`, whose `model` is
# a read-only property to mypy; the assignment works at runtime.
self.script = ScriptedAgent()
wiki_module.librarian.wrapped.model = FunctionModel(self.script.step)  # type: ignore[misc]

# In the test:
await Wiki.ref(WIKI_ID).ingest(self.context, transcript_id=...)
await self.script.done.wait()
```

Restore the original model in `asyncTearDown`.

### Environment variables

Set in `asyncSetUp`, restore in `asyncTearDown`:

```python
async def asyncSetUp(self) -> None:
    self._prev_admin_key = os.environ.get(STORE_ADMIN_KEY_ENV)
    os.environ[STORE_ADMIN_KEY_ENV] = ADMIN_KEY

async def asyncTearDown(self) -> None:
    await self.rbt.stop()
    if self._prev_admin_key is None:
        os.environ.pop(STORE_ADMIN_KEY_ENV, None)
    else:
        os.environ[STORE_ADMIN_KEY_ENV] = self._prev_admin_key
```

A variable that must exist before any import (an SDK that builds its
client at import time) goes in `conftest.py`
([`testing-project-setup.md`](testing-project-setup.md)).

### One harness test per user story

Name each test after the story
(`test_overdraft_is_rejected_with_overdraft_error`), give it one
external context, call through `Service.ref(id).method(context, ...)`,
and assert the user-observable outcome (what the UI would render), not
internal state shape. Not one test per servicer method.

## Never

- **`ReaderContext(...)` / `WriterContext(...)` in a test** — those are
  runtime-managed; use `create_external_context`.
- **Overriding `authorizer()` in a test subclass** — impersonate with
  `create_external_context_as`. Subclassing to mock *behavior* is fine.
- **Several denied mutations asserted from one context** — a
  `PermissionDenied` is not a declared error, so the context is marked
  uncertain and its next mutation fails with `IdempotencyUncertainError`.
  Use a fresh context per denial, or give each its own
  `.idempotently("...")` alias. Asserting a declared error costs
  nothing (cineloop, 1.4.1).
- **Polling with `asyncio.sleep`** — that tests the sleep; use
  `reactively()` or `retrieve`.
- **`anext()` without `asyncio.wait_for`** — a missing update hangs
  the suite.
- **Patching where a helper is defined** — patch where it is imported.

## Limits

- `create_external_context_as` mints through the app's OAuth server;
  call `up()` first.

## Scales as

- Not measured.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `IdempotencyUncertainError: Because we don't know if the mutation from calling` | An earlier call from this context failed with an undeclared error (often a denial) | Fresh context, or `.idempotently("...")` per call |
| `Property "model" defined in "AbstractAgent" is read-only [misc]` (mypy) | Assigning `agent.wrapped.model` in a test | `# type: ignore[misc]` on that line |

## See also

- [`testing-harness.md`](testing-harness.md) — `Reboot()`, `up()`, impersonation
- [`testing-features.md`](testing-features.md) — custom steps use these calls
- [`patterns-idempotency.md`](patterns-idempotency.md) — uncertain mutations explained
