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

Setting up or extending a Reboot app's test suite: Gherkin `.feature`
files in root `tests/`, run by `reboot.bdd` through `pytest`. Writing
scenarios: [testing-features.md](testing-features.md); browser
scenarios: [testing-web-app.md](testing-web-app.md); harness tests:
[testing-harness.md](testing-harness.md).

## Do this

Grow the template's passing suite (`build/templates/<front-door>/`) in this shape:

```
<app>/
├── api/                      # pydantic API definitions
├── backend/api/              # generated `_rbt` modules
├── backend/src/servicers/    # servicers
├── tests/
│   ├── posting.feature           # one feature per capability
│   ├── chat_room_test.py         # `application` fixture + `scenarios(...)`
│   ├── web_test.py               # the scenarios that open the web app
│   ├── posting.recordings/       # made by running; git-ignored
│   └── conftest.py               # only when needed, see below
├── .gitignore                # includes `*.recordings/`
├── pytest.ini
└── pyproject.toml
```

- **Feature file**: named for the activity (`transfers.feature`), not a state type.
- **Test module**: ends in `_test.py`, defines the `application`
  fixture (the `Application(...)` its scenarios run against), calls
  `scenarios('a.feature', 'b.feature')`. One module per application
  configuration (authorizers, a job off, a scripted LLM, web app
  served). Copy `tests/<app>_test.py`; with `oauth=`, its fixture passes
  `OAuth(provider=OAuthProviderByEnvironment(dev=development,
  prod=development), allowed_origins=[])`, because the harness is
  neither `rbt dev run` nor `rbt serve`.
- **Crash-and-recover test**
  ([testing-failure-recovery.md](testing-failure-recovery.md)): an
  `IsolatedAsyncioTestCase` in its own `_test.py` module.
- **`pytest.ini`** (copy it): `testpaths = tests`; `pythonpath` =
  `backend/src` (servicers), `backend/api` (generated `_rbt`), `api`
  (hand-written API, `from <pkg>.v1.<name> import SomeError`). Without
  `api`, import fails with a `ModuleNotFoundError` that looks like a
  codegen failure.
- **Dev dependencies** (template `pyproject.toml`): `reboot[dev]` at
  the `reboot` pin (registers built-in steps as a pytest plugin; nothing
  imports them), `pytest`, `mypy`. Web app scenarios add
  `playwright>=1.55.0`, `pytest-playwright>=0.7.1`, then
  `uv run playwright install chromium` once. `uv sync` installs the
  `dev` group; `[tool.uv.dev-dependencies]` is an accepted alias.
- **`conftest.py`** only when a module tests import eagerly needs an
  env var (an LLM client built at import); tests must still mock the
  real call. A stand-in for one module is an autouse fixture there.

```python
# tests/conftest.py
import os

os.environ.setdefault("ANTHROPIC_API_KEY", "test-placeholder")
```

**Run** from the project root:

```bash
uv run pytest                           # whole suite
uv run pytest tests/chat_room_test.py   # one module
uv run pytest -k "posts a message"      # one scenario by name
uv run pytest -m wip                    # or -m "not wip"
uv run pytest -v -s                     # with print() output
```

`@blocked` scenarios skip with their description as reason. Quiet
runs, or pass-alone/fail-in-suite: `lifecycle-dev-loop.md`.

## Never

- `ChatRoomServicer().send(...)` in a custom step or harness test — it
  bypasses identity, context, persistence and authorization. Use
  `world.context(user)` + `Service.ref(id).method(context, ...)` in a
  step ([testing-features.md](testing-features.md)),
  `rbt.create_external_context(...)` in a harness test.
- `pytest-asyncio` in the dev dependencies: `reboot.bdd` runs steps on
  the harness's loop and `IsolatedAsyncioTestCase` on its own; it conflicts with both.
- `oauth=OAuth(provider=...)` in a fixture without `allowed_origins`:
  every scenario fails (error below).
- Tests under `backend/tests/` with a `backend/.pytest.ini`: tests are the application's, in root `tests/`, with the root `pytest.ini`.
- Committing `*.recordings/`; check the `.gitignore` line when adding the first web app scenario.

## Limits

- Several `Reboot()` harness applications on one machine (pytest-xdist
  `-n auto`, `-n4`) hung silently at 1.6.0 in one large suite (zero CPU,
  no error, no timeout; unexplained). Parallelize by module (one
  application each); fall back to `-n0`; `pytest-timeout` turns a hang
  into a failure.
- Most apps need no `conftest.py`; its fixtures are shared by every module.

## Scales as

- Time is per-module app start-up plus scenario count; one application
  per module took a suite from 13 minutes to about 2 with `-n auto`
  (1.6.0, before the hang above returned).

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `` `OAuth` requires `allowed_origins=[...]` to be set explicitly in production `` | The fixture's `OAuth(...)` has no `allowed_origins`; the harness counts as production | `allowed_origins=[]`, or `[frontend.origin]` for browser scenarios |
| `ModuleNotFoundError: No module named '<pkg>.v1.<name>'` | `api` missing from `pytest.ini`'s `pythonpath` | Copy the template's `pytest.ini` |

## See also

- [testing-features.md](testing-features.md) — writing the scenarios
- [testing-web-app.md](testing-web-app.md) — browser scenarios and the `frontend` fixture
- [`build/templates/README.md`](../../build/templates/README.md) — every template file explained
