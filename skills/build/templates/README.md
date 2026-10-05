# Project templates

One minimal project per front door: every scaffold file verbatim, plus
the smallest API, servicer, `main.py`, feature file and test module that
build, type-check and pass one scenario. `tools/templates-smoke.sh`
builds both on every change. Copy a template — never retype a scaffold
file from memory or a reference — then replace the sample domain (a
counter) with the app's own.

## Copy

```sh
<plugin>/skills/build/templates/copy.sh <mcp-ui|web-app> <dest-dir> <project> <app> "<Title>"
# e.g.
<plugin>/skills/build/templates/copy.sh web-app . todo-list todo_list "Todo List"
```

`<plugin>` is the plugin root (holding `bin/rbt`). `copy.sh` copies the
tree (dotfiles included), renames paths containing `__app__`, fills the
placeholders, and refuses a destination that already has an `.rbtrc`.
Then:

```sh
uv sync
rbt generate
(cd frontend && npm install)   # `cd web` for a web app
rbt generate                   # again: the React bindings need node_modules
```

## Placeholders

| Placeholder | Form | Example | Used in |
| --- | --- | --- | --- |
| `__project__` | kebab-case project name | `todo-list` | `pyproject.toml` `name`, `.rbtrc` `--application-name`, `package.json` `name` (`__project__-web`) |
| `__app__` | snake_case API package and module | `todo_list` | `api/__app__/v1/__app__.py`, `servicers/__app__.py`, `tests/__app___test.py`, imports (`__app__.v1.__app___rbt`), the `.mypy.ini` ignore stanza, the React import path |
| `__Title__` | human-readable title | `Todo List` | `Application(title=...)`, `<title>`, docstrings |

A second API module needs its own `[mypy-<pkg>.v1.<name>_rbt]` stanza
in `.mypy.ini`.

## Files

Both front doors share the Python shell:

| File | What it is | Change when |
| --- | --- | --- |
| `.python-version` | `3.12`, the highest Python `rbt` supports (`bin/rbt`) | Never |
| `pyproject.toml` | `reboot==1.6.0`; dev group `reboot[dev]==1.6.0`, `mypy`, `pytest`, `types-protobuf`. No `[build-system]` (a virtual `uv` project) | Adding a runtime dependency; browser scenarios add `playwright` and `pytest-playwright` (`python/references/testing-web-app.md`); an LLM agent turns `reboot` into `reboot[anthropic]` (`python/references/agent-pydantic-ai.md`) |
| `.rbtrc` | Line-based `rbt` config: codegen paths, watch globs, `--application-name`, `--env-file`, `serve run` | Port or config changes (`python/references/lifecycle-rbtrc.md`) |
| `.mypy.ini` | Source roots on `mypy_path`, `explicit_package_bases`, an ignore stanza naming only the generated `_rbt` module | A new API module (one stanza each) |
| `pytest.ini` | `testpaths = tests`; `pythonpath` of `backend/src`, `backend/api`, `api` | Never |
| `.gitignore` | Dev state, generated code, `.env`, recordings, venv, `node_modules/`, frontend build | Never; the generated-code paths match `.rbtrc` |
| `FINDINGS.md` | The agent's log of surprises (wrong or silent skill, framework behaviour); the `report` skill files them upstream | Append items; never delete them |
| `api/__app__/v1/__app__.py` | Sample pydantic API | Always: the app's own types |
| `backend/src/servicers/__app__.py` | Sample servicers | Always |
| `backend/src/main.py` | `Application(...)` with `oauth=OAuth(provider=OAuthProviderByEnvironment(dev=Development(), prod=None), allowed_origins=[])` | Production provider and origins before deploy |
| `tests/counting.feature` | One `@wip` sample feature | Replace with the app's features (`feature` skill) |
| `tests/__app___test.py` | `application` fixture and `scenarios(...)` | Servicer list; one module per application configuration |

### `mcp-ui/` adds

| File | What it is |
| --- | --- |
| `backend/src/example_prompts.py` | The wizard's `ExamplePrompt`s, passed to `Application(example_prompts=...)` |
| `frontend/package.json` | React 18, TypeScript 5.9, Vite 6, `vite-plugin-singlefile`, the Reboot and MCP packages; `build` is `tsc -b && node build.mjs` |
| `frontend/vite.config.ts` | **Copy exactly.** Serves HMR for every UI under `/__/frontend/`; builds each UI to the nested `dist/mcp/<name>/index.html` the MCP server resolves |
| `frontend/build.mjs` | Discovers every `mcp/<name>/index.html` (and `web/`) and builds each |
| `frontend/tsconfig.json`, `tsconfig.app.json`, `tsconfig.node.json` | Split app / Vite-config projects; `@api/*` path alias |
| `frontend/vite-env.d.ts` | Vite client types (CSS modules, `import.meta.env`) |
| `frontend/mcp/clicker/` | One UI: `index.html`, `main.tsx`, `App.tsx`, `App.module.css`, `index.css`. Its directory is the `UI(path="frontend/mcp/clicker")` of `Counter.show`; rename both together |

### `web-app/` adds

| File | What it is |
| --- | --- |
| `web/package.json` | React 18, TypeScript 5.9, Vite 6, `@types/node`, the two Reboot packages; `build` is `tsc -b && vite build` |
| `web/vite.config.ts` | Stock config plus `resolve.dedupe`, `server.host: true`, a project port (`5273`), `strictPort: true` |
| `web/tsconfig.json`, `tsconfig.app.json`, `tsconfig.node.json` | Split app / Vite-config projects; `tsconfig.node.json` has `"types": ["node"]` |
| `web/.env.development` | `VITE_REBOOT_URL=http://localhost:9991` |
| `web/index.html`, `web/src/main.tsx` | Entry; `RebootClientProvider url={REBOOT_URL}` |
| `web/src/App.tsx` | Sign-in gate on `useUser()`, one reader and one mutation |
| `web/src/vite-env.d.ts` | Vite client types for `import.meta.env` |

## Versions

Pinned to what the plugin ships: Reboot `1.6.0` (`bin/rbt`
`REBOOT_VERSION`) and the frontend set `@reboot-dev/create-ui@1.6.0`
writes (`react`/`react-dom` `^18.2.0`, `typescript` `^5.9.2`, `vite`
`^6.3.5`, `@vitejs/plugin-react` `^4.7.0`, `zod` `^4.0.0`) — not the
React 19 / TypeScript 6 of `npm create vite@latest`. The `upgrade`
skill bumps every `1.6.0` here together.

## Smoke test

```sh
tools/templates-smoke.sh            # both front doors
SMOKE_FULL=1 tools/templates-smoke.sh web-app   # also run the scenario
```
