---
title: Spin Up Tests with the `Reboot()` Harness
impact: MEDIUM
impactDescription: Without the harness, Servicer methods can't be exercised end-to-end; with it misconfigured, tests hang, fail at call time, or test a different application
tags: testing, Reboot, harness, IsolatedAsyncioTestCase, setup, authorizer, libraries, impersonation, bearer-token, oauth, token-verifier, app_internal, fixture, initialize
step: tests
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: ""
---

# Spin Up Tests with the `Reboot()` Harness

## When you are here

You are writing a test that boots the application in-process. Reboot
ships the harness at `reboot.aio.tests.Reboot`. A feature file's
scenarios run on it through `reboot.bdd`, and that is where an
application's behaviour is tested ([`testing-features.md`](testing-features.md)).
The test module's `application` fixture is the `Application(...)`
passed to `rbt.up(...)` below. Use the harness directly from a
`unittest.IsolatedAsyncioTestCase` for what a scenario cannot say,
such as crashing the application mid-method
([`testing-failure-recovery.md`](testing-failure-recovery.md)). Pytest
discovers these classes automatically. Project wiring is covered in
[`testing-project-setup.md`](testing-project-setup.md).

## Do this

```python
import unittest
from chat_room.v1.chat_room_rbt import ChatRoom
from chat_room_servicer import ChatRoomServicer
from reboot.aio.applications import Application
from reboot.aio.external import ExternalContext  # for type hints
from reboot.aio.tests import Reboot


class TestChatRoom(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self) -> None:
        self.rbt = Reboot()
        await self.rbt.start()

    async def asyncTearDown(self) -> None:
        await self.rbt.stop()

    async def test_chat_room(self) -> None:
        await self.rbt.up(Application(servicers=[ChatRoomServicer]))

        context = self.rbt.create_external_context(name=f"test-{self.id()}")
        chat_room = ChatRoom.ref("testing-chat-room")

        await chat_room.send(context, message="Hello, World")

        response = await chat_room.messages(context)
        self.assertEqual(response.messages, ["Hello, World"])
```

Put `up()` in `asyncSetUp` when every test uses the same
`Application`, or in each test when configurations differ. The
harness exercises the full RPC path: production's context-type rules,
error semantics and serialization. If a test passes, the
wiring is correct, and it catches contract bugs that a manual
click-through takes minutes to surface.

**Register what `main.py` registers.** Pass the same `servicers=`,
the stdlib `libraries=[...]` (`OrderedMap`, `Queue`, … need theirs,
see `stdlib-*.md`), `legacy_grpc_servicers=[...]` for plain-gRPC
servicers in a mixed app, and the production `initialize=`. Import them
from one registry (`SERVICERS`, `libraries()`) that `main.py` and
every harness share, so no test file misses a new type:

```python
await self.rbt.up(
    Application(
        servicers=SERVICERS,
        libraries=libraries(),
        initialize=initialize,   # or a test-sized seed, below
    )
)
```

**Construct what `initialize` constructs.** Every singleton
`initialize` creates (chain, ledger, settings actor) must exist in the
test too. Either pass the production `initialize=`, or call the same
parameterised seed function with less data
([`lifecycle-seeding.md`](lifecycle-seeding.md)).

**Seed and call internal methods with an app-internal context.**
Methods whose rule is `is_app_internal()` (seed methods, and methods
only scheduled tasks or other actors call) are unreachable from user
contexts. Use
`self.rbt.create_external_context(name="internal", app_internal=True)`.
This is the test-side equivalent of `initialize`, and it is also how
to drive a scheduled method directly instead of waiting for it. It
impersonates the *application*, so never reuse it for calls that
should be attributed to a user.

**Test against the real authorizers: impersonate, don't disable.**
The harness runs production-mode authorization, even though
`rbt dev run` only warns about a missing `authorizer()`. Register the
real servicers and give each test context a verified identity:

```python
self.context = await self.rbt.create_external_context_as(
    name=f"test-{self.id()}",
    user_id="test-user",
)
```

`rbt.make_valid_oauth_access_token(user_id=...)` mints the raw token
for an `Authorization:` header. A denial means the test context lacks
the right identity (fix the test) or the authorizer has a bug (the
test caught it). Don't weaken the authorizer. A negative auth test uses a second context with a
different `user_id` and asserts the call aborts
([`testing-external-context.md`](testing-external-context.md)).

**Identity wiring.** Leave `oauth=` out of a test's `Application(...)`,
whatever the app type. `up()` then installs a test OAuth provider, so
`create_external_context_as` works with no wiring. That provider
rejects the browser sign-in flow, so tests impersonate instead.

- If the app has a production `token_verifier=`, keep it. Impersonation
  tokens verify first, and a bearer that a test builds by hand still
  flows through the app's verifier.
- If the app needs no identity (no `User` type, no identity rules), a
  plain `create_external_context(name=...)` is fine.
- To test an OAuth sign-in flow itself, pass the provider explicitly:
  `oauth=OAuth(provider=OAuthProviderForTest(<provider>))`, with
  `OAuthProviderForTest` from `reboot.aio.tests` and `OAuth` from
  `reboot.aio.auth.oauth`. Any `OAuth(...)` you pass needs
  `allowed_origins=` (`[]` for backend-only), because the harness is
  not `rbt dev run`.

**Auto-construct under auth.** Minting a token
(`create_external_context_as`, `make_valid_oauth_access_token`) calls
`_authenticated`, which constructs the user's `User`-shaped state. If no token was minted,
the first call into `User.ref(user_id)` aborts as unconstructed. To
construct one for a user with no context, or to deliver claims to
`set_claims`:

```python
await UserServicer._authenticated(
    self.rbt.create_external_context(name="internal", app_internal=True),
    state_id=self.user_id,
)
token = await self.rbt.make_valid_oauth_access_token(
    user_id=self.user_id, claims={"email": "alice@example.com"},
)
```

**Assert a typed error, and narrow it for `mypy`.** The `Aborted` type
is per method (`TaskList.AddTaskAborted`). Its `.error` is a union of
your declared errors and every framework error, so narrow it with
`assert isinstance`. `assertIsInstance` checks at runtime but does not
narrow for `mypy`.

```python
with self.assertRaises(TaskList.AddTaskAborted) as caught:
    await TaskList.ref(list_id).add_task(alice, title="one too many")
error = caught.exception.error
assert isinstance(error, QuotaExceededError)  # Narrows the union.
self.assertEqual(error.limit, 10)
```

**Race two mutations.** Use one external context per concurrent
caller, and a second context for the same user id when a user races
themselves. Set up a state where exactly one call can succeed (the
last slot under a quota). Gather with `return_exceptions=True` and
partition the results. Then **assert the invariant**, not just the
exception:

```python
for i in range(9):  # quota is 10; exactly one racer can win
    await TaskList.ref(list_a).add_task(self.alice, title=f"t{i}")
alice2 = await self.rbt.create_external_context_as(
    name=f"alice2-{self.id()}", user_id=ALICE,
)
results = await asyncio.gather(
    TaskList.ref(list_a).add_task(self.alice, title="race-a"),
    TaskList.ref(list_b).add_task(alice2, title="race-b"),
    return_exceptions=True,
)
failures = [r for r in results if isinstance(r, BaseException)]
self.assertEqual(len(results) - len(failures), 1)
self.assertIsInstance(failures[0], TaskList.AddTaskAborted)
profile = await User.ref(ALICE).profile(self.alice)
self.assertEqual(profile.open_task_count, 10)
```

"Exactly one wins" holds only if the invariant goes through one actor,
or one transaction covering every actor involved.

## Never

- **Calling servicer instances directly** (`ChatRoomServicer().send(...)`).
  There is no identity, context, persistence or authorization, so it
  tests nothing.
- **Overriding `authorizer()` to `allow()` for the suite.** That tests
  a different application. The legitimate use is narrow: pure
  behaviour of a type whose rules are covered by other tests. Say why
  in a comment, and keep at least one test on the real authorizers.
  Subclassing to mock *non-auth* behaviour is fine, such as an external
  call or the clock. Route every wall-clock read through one
  module-level `_now()` and patch that.
- **Reusing a context after asserting a denial.** A `PermissionDenied`
  is an undeclared abort, so the context is now uncertain, and the
  next mutation from it raises `IdempotencyUncertainError`. Use a
  throwaway context for each call expected to be denied (student-sor,
  1.5.0).
- **Holding a `ref()` across two contexts**, even serially. A
  `WeakReference` is bound to the first context that uses it. Hold ids,
  and call `Type.ref(id)` inline for each call.
- **Reusing actor ids across tests.** Embed `self.id()` in actor ids
  and context names. The harness is fresh per test, but this keeps
  traces identifiable.

## Limits

- **A failing `initialize` makes `up()` hang**, because it is retried
  forever. Pytest captures the retry warnings, so the run looks hung.
  Rerun with `pytest -s` ([`lifecycle-dev-loop.md`](lifecycle-dev-loop.md)).
- A servicer missing from `servicers=` is not caught at `up()`. The
  application starts, and the first call to that type fails with
  `Method not found!`.
- Effect validation is **on** in the harness by default. It re-runs
  writer and transaction bodies, so mutation-heavy tests pay roughly
  double, and call counters are inflated. Turn it off only for counting
  or benchmarking:
  `rbt.up(..., effect_validation=EffectValidation.DISABLED)`, with
  `EffectValidation` from `reboot.aio.contexts`.
- Parallel harness runs (`pytest -n auto`/`-n4`) have hung silently,
  at zero CPU with no output (reboot-crm, 1.6.0, cause unexplained).
  Give each run a timeout. Fall back to `-n0`.

## Scales as

- Each test boots and tears down a runtime, about 2 s even with
  nothing seeded. A full production seed per test can add about 30 s.
  Size the fixture to the assertion ([`lifecycle-seeding.md`](lifecycle-seeding.md)).
- Benchmark in the harness, before and after in the same process, with
  effect validation disabled. Check machine load first, and distrust a
  single sample (theater-chain, 1.4.1).

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `StateNotConstructed { requires_constructor: true }` | The test reached an actor that production's `initialize` constructs | Pass `initialize=`, or construct it in the fixture |
| `aborted with 'PermissionDenied': You are not authorized to call` | The harness enforces real authorizers, or a user context called an internal method | Impersonate with `create_external_context_as`, or use `app_internal=True` for internal calls |
| `StatusCode.UNIMPLEMENTED details = "Method not found!"` | The type's servicer is missing from this harness's `servicers=` | Register it, ideally from a shared registry |
| `IdempotencyUncertainError: Because we don't know if the mutation` | The context was reused after a denied or failed mutation | Use a fresh context for each expected failure |
| `has previously been used by a different` (`MixedContextsError`) | One `ref()` was used with two contexts | `Type.ref(id)` per call |
| `` `OAuth` requires `allowed_origins=[...]` to be set explicitly in production `` | A test passed `OAuth(...)` with no `allowed_origins` | Omit `oauth=`, or pass `allowed_origins=[]` |
| `ValueError: This application is already up` | `up()` was called twice | `await rbt.down()` first, and see [`testing-failure-recovery.md`](testing-failure-recovery.md) |

## See also

- [`testing-features.md`](testing-features.md): where behaviour is specified
- [`lifecycle-seeding.md`](lifecycle-seeding.md): test-sized parameterised seeds
- [`lifecycle-dev-loop.md`](lifecycle-dev-loop.md): debugging hangs and silent runs
