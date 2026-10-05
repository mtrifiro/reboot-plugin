---
title: Lay Out a Reboot Backend Test Suite
impact: MEDIUM
impactDescription: Without `reboot[dev]`, the pytest paths, and the git-ignore, the built-in steps are missing, generated `_rbt` modules can't be imported, and recordings get committed
tags: testing, pytest, layout, pyproject, conftest, uv, reboot-dev, gitignore, recordings, template
summary: "`tests/` layout; the template's `pytest.ini` (three paths, or generated `_rbt` imports fail) and fixture (`allowed_origins=[]`); `reboot[dev]`, no `pytest-asyncio`; never construct servicers directly."
step: tests
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: ""
---

# Lay Out a Reboot Backend Test Suite

## When you are here

You are setting up, or adding to, the test suite of a Reboot app:
where feature files and test modules go, `pytest.ini`, dev
dependencies, `conftest.py`, and how to run it. A Reboot app's tests
are Gherkin `.feature` files in `tests/` at the project root, run by
`reboot.bdd` through `pytest`. Writing scenarios is
[testing-features.md](testing-features.md); browser scenarios are
[testing-web-app.md](testing-web-app.md); harness tests are
[testing-harness.md](testing-harness.md).

## Do this

The template (`build/templates/<front-door>/`, see
[`build/templates/README.md`](../../build/templates/README.md)) ships
`pytest.ini`, one feature and one test module that pass. Grow it in
this shape:

```
<app>/
├── api/                      # pydantic API definitions
├── backend/api/              # generated `_rbt` modules
├── backend/src/servicers/    # servicers
├── tests/
│   ├── posting.feature           # one feature per capability
│   ├── moderation.feature
│   ├── chat_room_test.py         # `application` fixture + `scenarios(...)`
│   ├── web_test.py               # the scenarios that open the web app
│   ├── posting.recordings/       # made by running; git-ignored
│   └── conftest.py               # only when needed, see below
├── .gitignore                # includes `*.recordings/`
├── pytest.ini
└── pyproject.toml
```

- **A feature file** is named for the activity (`transfers.feature`),
  not a state type.
- **A test module** ends in `_test.py`, defines the `application`
  fixture returning the `Application(...)` its scenarios run against,
  and calls `scenarios('a.feature', 'b.feature')`. One module per
  application configuration (with authorizers, a job turned off, a
  scripted LLM, the web app served). Copy `tests/<app>_test.py`: for
  an app with `oauth=`, its fixture passes
  `OAuth(provider=OAuthProviderByEnvironment(dev=development,
  prod=development), allowed_origins=[])`, because the harness is
  neither `rbt dev run` nor `rbt serve`.
- **A crash-and-recover test**
  ([testing-failure-recovery.md](testing-failure-recovery.md)) is an
  `IsolatedAsyncioTestCase` in its own `_test.py` module.

**`pytest.ini`** (copy it) sets `testpaths = tests` so a bare `pytest`
runs the suite, and `pythonpath` to `backend/src` (servicers),
`backend/api` (generated `_rbt` modules) and `api` (the hand-written
API module, imported as `from <pkg>.v1.<name> import SomeError`).
Leave `api` out and the suite fails at import with a
`ModuleNotFoundError` that looks like a codegen failure.

**Dev dependencies** are in the template's `pyproject.toml`:
`reboot[dev]` at the same pin as `reboot` (it registers the built-in
steps as a pytest plugin, so no module imports them), `pytest`,
`mypy`. Scenarios that open the web app add `playwright>=1.55.0` and
`pytest-playwright>=0.7.1`, then `uv run playwright install chromium`
once. `uv sync` installs the `dev` group by default;
`[tool.uv.dev-dependencies]` is an accepted alias for the list.

**`conftest.py`** only when a module imported by tests eagerly needs
an environment variable (typically an LLM client built at import):

```python
# tests/conftest.py
import os

os.environ.setdefault("ANTHROPIC_API_KEY", "test-placeholder")
```

Tests must still mock the real call. A stand-in shared by one
module's scenarios is an autouse fixture in that module.

**Run** from the project root:

```bash
uv run pytest                           # whole suite
uv run pytest tests/chat_room_test.py   # one module
uv run pytest -k "posts a message"      # one scenario by name
uv run pytest -m wip                    # or -m "not wip"
uv run pytest -v -s                     # with print() output
```

A `@blocked` scenario is skipped with its description as the reason.
A run that goes quiet, or a test that passes alone and fails in the
suite: `lifecycle-dev-loop.md`.

## Never

- `ChatRoomServicer().send(...)` in a custom step or harness test — it
  bypasses identity, context, persistence and authorization. Call
  through the application: `world.context(user)` and
  `Service.ref(id).method(context, ...)` in a custom step
  ([testing-features.md](testing-features.md)),
  `rbt.create_external_context(...)` in a harness test.
- `pytest-asyncio` in the dev dependencies: `reboot.bdd` runs steps on
  the harness's loop and `IsolatedAsyncioTestCase` on its own;
  `pytest-asyncio` conflicts with both.
- `oauth=OAuth(provider=...)` in a fixture without `allowed_origins`:
  every scenario fails (error below).
- Tests under `backend/tests/` with a `backend/.pytest.ini`: tests are
  the application's, in root `tests/`, with the root `pytest.ini`.
- Committing `*.recordings/`; check the `.gitignore` line when adding
  the first web app scenario.

## Limits

- Several `Reboot()` harness applications on one machine (pytest-xdist
  `-n auto`, `-n4`) hung silently at 1.6.0 in one large suite: workers
  at zero CPU, no error, no timeout; never explained. One test module
  per application is the unit of parallelism; `-n0` (serial) is the
  fallback, and `pytest-timeout` turns a hang into a failure.
- Most apps need no `conftest.py`; a fixture there is shared by every
  module.

## Scales as

- Suite time is dominated by application start-up per module and the
  number of scenarios; splitting into one application per module took
  one suite from 13 minutes to about 2 with `-n auto` (observed at
  1.6.0, before the hang above returned).

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `` `OAuth` requires `allowed_origins=[...]` to be set explicitly in production `` | The fixture's `OAuth(...)` has no `allowed_origins`; the harness counts as production | `allowed_origins=[]`, or `[frontend.origin]` for browser scenarios |
| `ModuleNotFoundError: No module named '<pkg>.v1.<name>'` | `api` missing from `pytest.ini`'s `pythonpath` | Copy the template's `pytest.ini` |

## See also

- [testing-features.md](testing-features.md) — writing the scenarios
- [testing-web-app.md](testing-web-app.md) — browser scenarios and the `frontend` fixture
- [`build/templates/README.md`](../../build/templates/README.md) — every template file explained
