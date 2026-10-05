---
title: Set Up a Reboot Python Project
impact: CRITICAL
impactDescription: Project won't build or run without the right files in place
tags: project-setup, pyproject, python-version, dependencies, layout, gitignore, mypy, template
summary: "Never add `__init__.py` or edit `*_rbt.py`; copy `build/templates/<front-door>/`; mypy sees `self.state` as `Any`: typed locals."
step: shell
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: ""
---

# Set Up a Reboot Python Project

## When you are here

Creating a Reboot Python project, or checking its layout, dependencies,
`.gitignore` or type-check config. `.rbtrc`:
[`lifecycle-rbtrc.md`](lifecycle-rbtrc.md); tests and `pytest.ini`:
[`testing-project-setup.md`](testing-project-setup.md); front-door
deltas: `mcp-ui/references/project-shell.md`,
`web-app/references/react-client.md`.

## Do this

Copy the front door's template; don't retype the files:

```sh
<plugin>/skills/build/templates/copy.sh <mcp-ui|web-app> . <project> <app> "<Title>"
```

Backend-only: copy `web-app`, delete `web/` and the `web/` lines of
`.rbtrc` and `.gitignore`. Placeholders and files:
[`build/templates/README.md`](../../build/templates/README.md). Layout:

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

Why:

- **`pyproject.toml`** — runtime dep only `reboot==1.6.0` (what an app
  packaged for `rbt serve` installs); `dev` group: `reboot[dev]==1.6.0`
  (runs `reboot.bdd` and the dashboard; `rbt dashboard` refuses to start
  without it, `rbt dev run` warns), `mypy`, `pytest`, `types-protobuf`.
  `name` and `version` required (`uv` won't sync without them). **No
  `[build-system]` table**: a virtual `uv` project, so `uv sync`
  installs deps and the default `dev` group into `.venv` without
  building the app. LLM SDKs are extras: `reboot[anthropic]==1.6.0`
  ([`agent-pydantic-ai.md`](agent-pydantic-ai.md)).
- **`.gitignore`** — `.rbt/` (dev state), generated `backend/api/` and
  React output (`frontend/api/` or `web/src/api/`), `.env`,
  `*.recordings/`, venv and caches, `node_modules/`, the frontend build.
  Keep the frontend paths matching `.rbtrc`'s `generate --react=`. A
  fresh clone (and CI) runs `rbt generate` before anything imports or
  type-checks; `rbt dev run` regenerates on its own.
- **`.mypy.ini`** — with no `__init__.py`,
  `mypy_path = tests:backend/src:backend/api:api` plus
  `explicit_package_bases` lets mypy resolve
  `from <app>.v1.<app>_rbt import ...`; the root `api` entry resolves the
  hand-written API module. The ignore stanza names only the generated
  module (`[mypy-<app>.v1.<app>_rbt]`), one per API module. A blanket
  `[mypy-<app>.v1.*]` or a missing `api` entry makes every API-module
  import `Any` while mypy still says "Success".

### Type-check what you write

After any Python change in `backend/`, run from the project root and fix
every error; green mypy plus passing `uv run pytest` is done:

```bash
uv run mypy backend/ tests/
```

mypy does **not** check `self.state` or generated request types inside a
servicer: `_rbt.py` declares `State` (and each `<Method>Request`) as
`typing.cast(type, ...)`, read as `Any` (`reveal_type(self.state)` →
`Revealed type is "Any"`), so a misspelled field passes. Bind the
hand-written models to typed locals:

```python
from <app>.v1.<app> import CounterState, IncrementRequest

    async def increment(self, context, request: Counter.IncrementRequest) -> None:
        state: CounterState = self.state
        req: IncrementRequest = request
        state.value += req.amount   # now `state.valeu` is an error
```

Prove the config live with `reveal_type` on a typed local (names your
class) or a misspelled field on one (`has no attribute`), never via
`self.state`.

## Never

- `__init__.py` anywhere — not in `api/` (confuses `rbt generate`'s
  package detection), `backend/` or `tests/`. mypy resolves imports via
  `explicit_package_bases`, pytest via `pytest.ini`, and `rbt` sets the
  runtime `PYTHONPATH`.
- Hand-editing `backend/api/<app>/v1/<app>_rbt.py` (or anything under
  `frontend/api/` / `web/src/api/`): `rbt generate` overwrites it.
  Change the API definition.
- Committing generated code or `.rbt/`. If tracked,
  `git rm -r --cached backend/api frontend/api`.
- A nonstandard layout (entry point other than `backend/src/main.py`,
  API outside `api/`): `.rbtrc`, the template and every reference
  assume the canonical one.
- A `[tool.rye]` table: move dev deps into `[dependency-groups].dev`,
  drop the duplicated `reboot`, add `name`/`version`, replace
  `requirements*.lock` with `uv lock`.

## Limits

- Python 3.10+; the template pins `.python-version` to `3.12`, the
  highest `bin/rbt` supports.
- `reboot`, `reboot[dev]` (and the frontend's `@reboot-dev/*`) pin the
  same exact version as the `rbt` CLI; a mismatch makes the app refuse
  to start (`upgrade` skill).
- mypy doesn't type `self.state` or generated request types (above);
  verified at 1.6.0.

## Scales as

- mypy on the template: seconds; the suite on a real app: minutes —
  type-check first. Generated `_rbt.py` grows with the API (~14,000
  lines for the two-type template at 1.6.0); the ignore stanza skips it.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `Revealed type is "Any"` | `reveal_type(self.state)`: the generated alias is opaque to mypy | Annotate a typed local with the hand-written model |
| `Library stubs not installed for "grpc"` | mypy ran without the project-root `.mypy.ini` (observed at 1.6.0: it then checks the generated code) | Run from the project root with the template's `.mypy.ini` |

## See also

- [`lifecycle-rbtrc.md`](lifecycle-rbtrc.md) — the `.rbtrc` format
- [`testing-project-setup.md`](testing-project-setup.md) — `pytest.ini` and test layout
- [`build/templates/README.md`](../../build/templates/README.md) — every template file explained
