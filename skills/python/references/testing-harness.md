---
title: Spin Up Tests with the `Reboot()` Harness
impact: MEDIUM
impactDescription: Without the harness, Servicer methods can't be exercised end-to-end; with it misconfigured, tests hang, fail at call time, or test a different application
tags: testing, Reboot, harness, IsolatedAsyncioTestCase, setup, authorizer, libraries, impersonation, bearer-token, oauth, token-verifier, app_internal, fixture, initialize
summary: "Disabling authorizers or calling servicers directly tests nothing; register what `main.py` does, construct what `initialize` does, impersonate users."
step: tests
applies: [mcp-ui, web-app, backend-only]
always: false
when: "writing custom steps"
verified: 1.6.0
docs: ""
---

# Spin Up Tests with the `Reboot()` Harness

## When you are here

Writing a test that boots the app in-process with the harness,
`reboot.aio.tests.Reboot`. Feature-file scenarios run on it through
`reboot.bdd`, and that is where behavior is tested
([`testing-features.md`](testing-features.md)); the test module's
`application` fixture is the `Application(...)` passed to `rbt.up(...)`.
Use the harness directly from a `unittest.IsolatedAsyncioTestCase`
(pytest discovers it) only for what a scenario cannot say, such as a
mid-method crash ([`testing-failure-recovery.md`](testing-failure-recovery.md)).
Project wiring: [`testing-project-setup.md`](testing-project-setup.md).

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

`up()` goes in `asyncSetUp` when every test shares the `Application`,
else in each test. The harness runs the full RPC path (production
context-type rules, error semantics, serialization), so it catches
contract bugs a click-through takes minutes to find.

**Register what `main.py` registers**: the same `servicers=`, stdlib
`libraries=[...]` (`OrderedMap`, `Queue`, … need theirs, see
`stdlib-*.md`), `legacy_grpc_servicers=[...]` for plain-gRPC servicers
in a mixed app, and the production `initialize=`. Import them from one
registry (`SERVICERS`, `libraries()`) shared by `main.py` and every
harness, so no test misses a new type:

```python
await self.rbt.up(
    Application(
        servicers=SERVICERS,
        libraries=libraries(),
        initialize=initialize,   # or a test-sized seed, below
    )
)
```

**Construct what `initialize` constructs.** Every singleton it creates
(chain, ledger, settings actor) must exist in the test: pass the
production `initialize=`, or call the same parameterized seed with less
data ([`lifecycle-seeding.md`](lifecycle-seeding.md)).

**Seed and call internal methods with an app-internal context**:
`self.rbt.create_external_context(name="internal", app_internal=True)`.
Methods ruled `is_app_internal()` (seeds, methods only scheduled tasks
or other actors call) are unreachable from user contexts. This is the
test-side `initialize`, and drives a scheduled method directly instead
of waiting. It impersonates the *application*; never use it for calls
attributed to a user.

**Test against the real authorizers: impersonate, don't disable.** The
harness enforces production-mode authorization (`rbt dev run` only
warns about a missing `authorizer()`). Register the real servicers and
give each context a verified identity:

```python
self.context = await self.rbt.create_external_context_as(
    name=f"test-{self.id()}",
    user_id="test-user",
)
```

`rbt.make_valid_oauth_access_token(user_id=...)` mints a raw token for
an `Authorization:` header. A denial means the test lacks the right
identity (fix the test) or the authorizer has a bug; don't weaken the
authorizer. A negative auth test uses a second context with another
`user_id` and asserts the abort
([`testing-external-context.md`](testing-external-context.md)).

**Identity wiring.** Leave `oauth=` out of a test's `Application(...)`,
whatever the app type: `up()` installs a test OAuth provider, so
`create_external_context_as` works unwired. That provider rejects the
browser sign-in flow; tests impersonate instead.

- Keep a production `token_verifier=`: impersonation tokens verify
  first, and a hand-built bearer flows through the app's verifier.
- No identity needed (no `User` type, no identity rules): plain
  `create_external_context(name=...)`.
- To test an OAuth sign-in flow itself:
  `oauth=OAuth(provider=OAuthProviderForTest(<provider>))`
  (`OAuthProviderForTest` from `reboot.aio.tests`, `OAuth` from
  `reboot.aio.auth.oauth`). Any `OAuth(...)` needs `allowed_origins=`
  (`[]` for backend-only), because the harness is not `rbt dev run`.

**Auto-construct under auth.** Minting a token
(`create_external_context_as`, `make_valid_oauth_access_token`) calls
`_authenticated`, which constructs the user's `User`-shaped state;
without one, the first call into `User.ref(user_id)` aborts as
unconstructed. To construct for a user with no context, or deliver
claims to `set_claims`:

```python
await UserServicer._authenticated(
    self.rbt.create_external_context(name="internal", app_internal=True),
    state_id=self.user_id,
)
token = await self.rbt.make_valid_oauth_access_token(
    user_id=self.user_id, claims={"email": "alice@example.com"},
)
```

**Assert a typed error, narrowed for `mypy`.** `Aborted` is per method
(`TaskList.AddTaskAborted`); its `.error` unions your declared errors
with every framework error. Narrow with `assert isinstance`;
`assertIsInstance` checks but does not narrow.

```python
with self.assertRaises(TaskList.AddTaskAborted) as caught:
    await TaskList.ref(list_id).add_task(alice, title="one too many")
error = caught.exception.error
assert isinstance(error, QuotaExceededError)  # Narrows the union.
self.assertEqual(error.limit, 10)
```

**Race two mutations.** One external context per concurrent caller (a
second context for the same user id when a user races themselves). Set
up a state where exactly one call can succeed, gather with
`return_exceptions=True`, partition, then **assert the invariant**, not
just the exception:

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

- **Calling servicer instances directly** (`ChatRoomServicer().send(...)`):
  no identity, context, persistence or authorization; it tests nothing.
- **Overriding `authorizer()` to `allow()` for the suite.** It tests
  a different app. Only for pure behavior of a type whose rules other
  tests cover; say why in a comment and keep one test on the real
  authorizers. Mocking *non-auth* behavior by subclass is fine (an
  external call, the clock: route every wall-clock read through one
  module-level `_now()` and patch that).
- **Reusing a context after asserting a denial** — its next mutation
  raises `IdempotencyUncertainError` (`testing-external-context.md` §
  Never; student-sor, 1.5.0).
- **Holding a `ref()` across two contexts**, even serially — a
  `WeakReference` binds to the first context that uses it. Hold ids;
  call `Type.ref(id)` inline per call.
- **Reusing actor ids across tests.** Embed `self.id()` in actor ids
  and context names; the harness is fresh per test, but traces stay
  identifiable.

## Limits

- **A failing `initialize` makes `up()` hang** (retried forever; pytest
  captures the warnings). Rerun with `pytest -s`
  ([`lifecycle-dev-loop.md`](lifecycle-dev-loop.md)).
- A servicer missing from `servicers=` isn't caught at `up()`; the
  first call to that type fails `Method not found!`. Take the list
  from `servicers/registry.py`
  ([`lifecycle-application-entry.md`](lifecycle-application-entry.md))
  so no harness can miss one.
- Effect validation is **on** by default: writer and transaction
  bodies re-run, so mutation-heavy tests cost roughly double and call
  counters inflate. Disable only for counting or benchmarking:
  `rbt.up(..., effect_validation=EffectValidation.DISABLED)`
  (`EffectValidation` from `reboot.aio.contexts`).
- Parallel harness runs (`pytest -n auto`/`-n4`) have hung silently at
  zero CPU (reboot-crm, 1.6.0, unexplained). Give each run a timeout;
  fall back to `-n0`.
- Scenarios spend their time parked waiting for the application to
  become ready, not on CPU, so parallel runs (`-n4`, concurrent files)
  are no faster overall and hang or slow more (reboot-crm, 1.6.0). One
  `Reboot()` per file, files in sequence.

## Scales as

- Each test boots and tears down a runtime: about 2 s with nothing
  seeded; a full production seed can add about 30 s. Size the fixture
  to the assertion ([`lifecycle-seeding.md`](lifecycle-seeding.md)).
- Benchmark in the harness, before and after in one process, effect
  validation disabled; check machine load and distrust a single sample
  (theater-chain, 1.4.1).

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `StateNotConstructed { requires_constructor: true }` | The test reached an actor that production's `initialize` constructs | Pass `initialize=`, or construct it in the fixture |
| `aborted with 'PermissionDenied': You are not authorized to call` | The harness enforces real authorizers, or a user context called an internal method | Impersonate with `create_external_context_as`, or use `app_internal=True` for internal calls |
| `StatusCode.UNIMPLEMENTED details = "Method not found!"` | The type's servicer is missing from this harness's `servicers=`; or a watcher restart mid-suite, or (observed, unexplained) a start-up race | Register it, ideally from a shared registry; stop the watcher; rerun the file alone |
| `IdempotencyUncertainError: Because we don't know if the mutation` | The context was reused after a denied or failed mutation | Use a fresh context for each expected failure |
| `has previously been used by a different` (`MixedContextsError`) | One `ref()` was used with two contexts | `Type.ref(id)` per call |
| `ValueError: This application is already up` | `up()` was called twice | `await rbt.down()` first, and see [`testing-failure-recovery.md`](testing-failure-recovery.md) |
| `Error in sys.excepthook:` / `Original exception was:` after the run | Teardown noise with no payload | Ignore it; the summary line above it is the result |
| pytest ends with no summary line and exit 0 | The run died (an `F` may already be on screen) | Treat it as failed; rerun the file alone; `pytest-timeout` (the templates) fails a hang on its own |
| `Unimplemented` 404s, hangs, or a bare `TimeoutError` after about 45 s from `DatabaseClient`, on macOS | Test servers bind dual-stack `0.0.0.0`, and macOS hands their ports to ones an orphaned Envoy holds on IPv4 | Clear orphans first (`scripts/doctor.sh`); in `conftest.py`, `server_managers.EVERY_LOCAL_NETWORK_ADDRESS = "127.0.0.1"` |

## See also

- [`testing-features.md`](testing-features.md): where behavior is specified
- [`lifecycle-seeding.md`](lifecycle-seeding.md): test-sized parameterized seeds
- [`lifecycle-dev-loop.md`](lifecycle-dev-loop.md): debugging hangs and silent runs
