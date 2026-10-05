---
title: Set Up a Reboot Python Project
impact: CRITICAL
impactDescription: Project won't build or run without the right files in place
tags: project-setup, pyproject, python-version, dependencies, layout, gitignore, mypy, template
summary: "Copy `build/templates/<front-door>/`: layout, `pyproject.toml`, `.gitignore`, `.mypy.ini`. No `__init__.py`; never edit `*_rbt.py`; mypy sees `self.state` as `Any` — use typed locals."
step: shell
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: ""
---

# Set Up a Reboot Python Project

## When you are here

You are creating a Reboot Python project, or checking one's layout,
dependencies, `.gitignore` or type-check config. The `.rbtrc` format
is [`lifecycle-rbtrc.md`](lifecycle-rbtrc.md); the test layout and
`pytest.ini` are [`testing-project-setup.md`](testing-project-setup.md);
front-door deltas are `mcp-ui/references/project-shell.md` and
`web-app/references/react-client.md`.

## Do this

Copy the template for the front door; do not retype the files:

```sh
<plugin>/skills/build/templates/copy.sh <mcp-ui|web-app> . <project> <app> "<Title>"
```

A backend-only project copies `web-app` and deletes `web/` and the
`web/` lines of `.rbtrc` and `.gitignore`. The placeholders and every
file are listed in
[`build/templates/README.md`](../../build/templates/README.md). The
layout it produces:

```
<project>/
  .python-version .rbtrc .gitignore .mypy.ini pytest.ini pyproject.toml
  api/<app>/v1/<app>.py          # hand-written pydantic API (`generate api/`)
  backend/
    api/                         # `rbt generate --python` output, git-ignored
    src/main.py                  # application entry
    src/servicers/<app>.py       # servicers
  tests/<capability>.feature, tests/<app>_test.py
  frontend/ (mcp-ui) or web/ (web-app)
```

Why the shell files are shaped the way they are:

- **`pyproject.toml`** — `reboot==1.6.0` is the only runtime
  dependency; the `dev` group adds `reboot[dev]==1.6.0` (what
  `reboot.bdd` and the dashboard run on; `rbt dashboard` refuses to
  start without it, `rbt dev run` warns), `mypy`, `pytest`,
  `types-protobuf`. `name` and `version` are required (`uv` refuses to
  sync without them). There is **no `[build-system]` table**: that
  makes it a virtual `uv` project, so `uv sync` installs the
  dependencies and the default `dev` group into `.venv` without
  building the app. An application packaged for `rbt serve` installs
  plain `reboot`. An LLM provider SDK comes as an extra,
  `reboot[anthropic]==1.6.0` ([`agent-pydantic-ai.md`](agent-pydantic-ai.md)).
- **`.gitignore`** — `.rbt/` (dev state), the generated `backend/api/`
  and React output (`frontend/api/` or `web/src/api/`), `.env`,
  `*.recordings/`, the venv and caches, `node_modules/` and the
  frontend build. Each front door's template names its own frontend
  paths; keep them matching `.rbtrc`'s `generate --react=`. Because
  generated code is ignored, a fresh clone (and CI) runs
  `rbt generate` before anything imports or type-checks;
  `rbt dev run` regenerates on its own.
- **`.mypy.ini`** — generated modules and servicers have no
  `__init__.py`, so `mypy_path = tests:backend/src:backend/api:api`
  plus `explicit_package_bases` is what lets mypy resolve
  `from <app>.v1.<app>_rbt import ...`. The project-root `api` entry
  resolves the hand-written API module, and the ignore stanza names
  only the generated module (`[mypy-<app>.v1.<app>_rbt]`). A blanket
  `[mypy-<app>.v1.*]` or a missing `api` entry makes every import from
  the API module `Any` while mypy still says "Success". Add one stanza
  per API module.

### Type-check what you write

After any Python change in `backend/`, run from the project root and
fix every error; a green mypy plus a passing `uv run pytest` is the
bar for done:

```bash
uv run mypy backend/ tests/
```

mypy checks the request/response classes and the hand-written models,
but **not `self.state` or the generated request types inside a
servicer**: the generated `_rbt.py` declares `State` (and each
`<Method>Request`) as `typing.cast(type, ...)`, which mypy reads as
`Any`. `reveal_type(self.state)` prints `Revealed type is "Any"`, and
a misspelled field passes. Bind the hand-written models to typed
locals where it matters:

```python
from <app>.v1.<app> import CounterState, IncrementRequest

    async def increment(self, context, request: Counter.IncrementRequest) -> None:
        state: CounterState = self.state
        req: IncrementRequest = request
        state.value += req.amount   # now `state.valeu` is an error
```

To confirm the config is live, `reveal_type` a typed local (it must
name your class) or misspell a field on one (mypy must report
`has no attribute`). A bogus attribute on `self.state` proves nothing.

## Never

- `__init__.py` anywhere — not in `api/` (it confuses `rbt generate`'s
  package detection), not under `backend/` or `tests/`. mypy resolves
  imports through `explicit_package_bases`, pytest through
  `pytest.ini`, and `rbt` sets the runtime `PYTHONPATH`.
- Hand-editing `backend/api/<app>/v1/<app>_rbt.py` (or anything under
  `frontend/api/` / `web/src/api/`): every `rbt generate` overwrites
  it. Change the API definition instead.
- Committing generated code or `.rbt/`. If it is tracked,
  `git rm -r --cached backend/api frontend/api`.
- A nonstandard layout (an entry point other than `backend/src/main.py`,
  API definitions outside `api/`): `.rbtrc`, the template and every
  reference assume the canonical one.
- A `[tool.rye]` table: migrate dev dependencies into
  `[dependency-groups].dev`, drop the duplicated `reboot`, add
  `name`/`version`, and replace `requirements*.lock` with `uv lock`.

## Limits

- Python 3.10+; the template pins `.python-version` to `3.12`, the
  highest `bin/rbt` supports.
- `reboot` and `reboot[dev]` (and the frontend's `@reboot-dev/*`) pin
  the same exact version as the `rbt` CLI; a mismatch makes the
  application refuse to start (`upgrade` skill).
- mypy does not type `self.state` or generated request types (above);
  verified at 1.6.0.

## Scales as

- `uv run mypy backend/ tests/` on the template takes seconds; the
  test suite takes minutes on a real app, so type-check first.
  Generated `_rbt.py` grows with the API (about 14,000 lines for the
  two-type template at 1.6.0) and is skipped by the ignore stanza.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `Revealed type is "Any"` | `reveal_type(self.state)`: the generated alias is opaque to mypy | Annotate a typed local with the hand-written model |
| `Library stubs not installed for "grpc"` | mypy ran without the project-root `.mypy.ini` (observed at 1.6.0: it then checks the generated code) | Run from the project root with the template's `.mypy.ini` |

## See also

- [`lifecycle-rbtrc.md`](lifecycle-rbtrc.md) — the `.rbtrc` format
- [`testing-project-setup.md`](testing-project-setup.md) — `pytest.ini` and test layout
- [`build/templates/README.md`](../../build/templates/README.md) — every template file explained
