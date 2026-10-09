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

`both` is the dual-frontend app: the `mcp-ui` template plus the SPA in
`frontend/web/` (see "`both/` adds" below).

## Placeholders

| Placeholder | Form | Example | Used in |
| --- | --- | --- | --- |
| `__project__` | kebab-case project name | `todo-list` | `pyproject.toml` `name`, `.rbtrc` `--application-name`, `package.json` `name` (`__project__-web`) |
| `__app__` | snake_case API package and module | `todo_list` | `api/__app__/v1/__app__.py`, `servicers/__app__.py`, `tests/__app___test.py`, imports (`__app__.v1.__app___rbt`), the `.mypy.ini` ignore stanza, the React import path |
| `__Title__` | human-readable title | `Todo List` | `Application(title=...)`, `<title>`, docstrings |
| `__Initial__` | the title's first letter, capitalized | `T` | the placeholder favicon in the web app's `index.html` |

A second API module needs its own `[mypy-<pkg>.v1.<name>_rbt]` stanza
in `.mypy.ini`.

## Files

Both front doors share the Python shell:

| File | What it is | Change when |
| --- | --- | --- |
| `.python-version` | `3.12`, the highest Python `rbt` supports (`bin/rbt`) | Never |
| `pyproject.toml` | `reboot==1.6.0`; dev group `reboot[dev]==1.6.0`, `mypy`, `pytest`, `types-protobuf`. No `[build-system]` (a virtual `uv` project) | Adding a runtime dependency; browser scenarios add `playwright` and `pytest-playwright` (`python/references/testing-web-app.md`); an LLM agent turns `reboot` into `reboot[anthropic]` (`python/references/agent-pydantic-ai.md`) |
| `.rbtrc` | Line-based `rbt` config: codegen paths, watch globs, `--application-name`, `--env-file`, `serve run` | Port or config changes (`python/references/lifecycle-rbtrc.md`) |
| `.mypy.ini` | Source roots (and `scripts`) on `mypy_path`, `explicit_package_bases`, an ignore stanza naming only the generated `_rbt` module | A new API module (one stanza each) |
| `pytest.ini` | `testpaths = tests`; `pythonpath` of `backend/src`, `backend/api`, `api`, `scripts` (so the backup test imports `restore`) | Never |
| `.gitignore` | Dev state, generated code, `.env`, `.deploy.env`, recordings, venv, `node_modules/`, frontend build, `.reboot/`, `exports/` (backups: every user's data) | Never; the generated-code paths match `.rbtrc` |
| `AGENTS.md` | The map for a coding agent: where each concept lives, how to run, test and deploy, and the rules that cost the most when broken | When a file moves, a command changes or a rule is learned; a new state type, front door or script adds its row |
| `CLAUDE.md` | One line, `@AGENTS.md`, so Claude Code reads the same file every other agent does | Never; put everything in `AGENTS.md` |
| `FINDINGS.md` | The agent's log of surprises (wrong or silent skill, framework behavior); the `report` skill files them upstream | Append items; never delete them |
| `api/__app__/v1/__app__.py` | Sample pydantic API | Always: the app's own types |
| `backend/src/servicers/__app__.py` | Sample servicers | Always |
| `backend/src/main.py` | `Application(...)` with `oauth=OAuth(provider=OAuthProviderByEnvironment(dev=Development(), prod=None), allowed_origins=[])` | Production provider and origins before deploy |
| `tests/counting.feature` | One `@wip` sample feature | Replace with the app's features (`feature` skill) |
| `tests/__app___test.py` | `application` fixture and `scenarios(...)` | Servicer list; one module per application configuration |
| `tests/run_progress.py`, `tests/conftest.py` | Records how far a test run is in `.reboot/test-run.json` (gitignored), which the Reboot band reads; `conftest.py` imports its hooks (`python/references/testing-project-setup.md`, "Test-run progress") | Never |
| `scripts/deploy.sh`, `scripts/api_removals.py` | Every production deploy: a pushed commit, an additive API, `rbt cloud up` and the revision serving, the frontend built from the commit and published, a ledger line (`deploy` skill) | Never; settings go in `deploy/config` |
| `deploy/config` | The deploy's settings: Cloud app name and size, branch, frontend directories, Pages project, site address | On the first deploy (`deploy` skill, Step 2) |
| `scripts/backup.sh`, `scripts/restore.py`, `scripts/compare_exports.py`, `scripts/migrations/rules.py` | Back up (`rbt export`, a manifest, an empty export refused), restore into an expunged app (dry run first, checked against this checkout's API), prove nothing was lost; a migration composes `rules.py` (`python/references/lifecycle-backup-restore.md`) | `restore.py`'s three settings (`MUST_BE_EMPTY`, `BOOT_TASKS`, `RETIRED_PACKAGES`) once the app has a boot task; a migration per breaking release |
| `deploy/before-backend` | Run by `deploy.sh` before `rbt cloud up`: `scripts/backup.sh prod`, skipped only on the first deploy | Add the project's own pre-deploy steps below the backup |
| `tests/backup_restore_test.py` | The round trip (export, fresh app, `restore.py`'s passes, import, compare) against the harness, and a removed field caught before sending | Its `seed` when the sample type goes |
| `deploy/api-exceptions.md` | API removals Reboot allows, approved one line each for `api_removals.py` | Only to approve a removal; delete it once shipped |

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
| `frontend/mcp/styles.css` | The web app's tokens and classes (Reboot's brand by default) with system fonts (the `.ui` rule resets `--font-*`), shared by every UI (`mcp-ui/references/ui-design.md`) |
| `frontend/mcp/host-theme.ts` | `useHostTheme()`: applies the host's light/dark theme and follows changes |

### `web-app/` adds

| File | What it is |
| --- | --- |
| `web/package.json` | React 18, TypeScript 5.9, Vite 6, `@types/node`, `zod` 4, the two Reboot packages pinned to the backend's `reboot`; `build` is `tsc -b && vite build`. npm installs the `@bufbuild/protobuf` peer itself |
| `web/vite.config.ts` | Stock config plus `resolve.dedupe`, `server.host: true`, a project port (`5273`), `strictPort: true` |
| `web/tsconfig.json`, `tsconfig.app.json`, `tsconfig.node.json` | Split app / Vite-config projects (React 18 / TypeScript 5); `tsconfig.node.json` has `"types": ["node"]`; the app half includes `src/`, generated client and all, and type-checks cleanly at 1.6.0 |
| `web/.env.development` | `VITE_REBOOT_URL=http://localhost:9991` |
| `web/index.html`, `web/src/main.tsx` | Entry; a placeholder favicon in `index.html` (the title's initial on the accent; swap in the brand's mark); `RebootClientProvider url={REBOOT_URL}`; imports Reboot's typefaces from `@fontsource` (Space Grotesk, DM Sans, DM Mono; no font CDN), then `styles.css` |
| `web/src/styles.css` | Design tokens in Reboot's brand by default (cream page, navy ink and accent, sage tint, `--good`/`--warn`/`--bad` for one data dimension; light and dark; `web-app/references/ui-design.md`, "The default look"), base elements, and classes for the page anatomy (`topbar`, `page-head`, `stats`), each primary view (`filter-panel`/`list-card`/`row`, `board`, `chart`, `feed`), detail (`drawer`, `kv`) and actions (`confirm-bar`, `notice`), listed at its top (`web-app/references/ui-design.md`) |
| `web/src/App.tsx` | Sign-in gate on `useUser()`, one reader and one mutation, laid out in the page anatomy (title block with a lede, then a stat tile) |
| `web/src/theme.tsx` | `ThemeToggle` (light/dark, saved in `localStorage`, OS setting until chosen) and `applySavedTheme()`, called in `main.tsx` before render |
| `web/src/vite-env.d.ts` | Vite client types for `import.meta.env` |
| `tests/conftest.py` | The look steps (phone fit, no loading text, own fonts, light and dark, no clipped labels); defined only when Playwright is installed (`python/references/testing-web-app.md`, "Look steps") |
| `scripts/screenshots.py` | Signs in through the Development picker and saves every route at 1440 and 375 px, light and dark, to `screenshots/` (gitignored) for the design review (`web-app/references/ui-design.md`, principle 12) |

### `both/` adds

The `mcp-ui` template with a `list_counters` reader on `User` (so the
web app can find the user's counters) and the SPA beside the MCP UIs:

| File | What it is |
| --- | --- |
| `frontend/web/index.html`, `src/main.tsx` | The SPA entry, with the placeholder favicon; served by the backend at `/__/frontend/web/`, so the provider's default origin is the backend (no `.env.development`) |
| `frontend/web/src/App.tsx` | Sign-in gate, the user's counters as cards, `useCounter({ id })` per card; imports the one generated client via `@api/…` |
| `frontend/styles.css` | The one shared stylesheet (the same tokens and classes as `web-app/`); `web/src/styles.css` and `mcp/styles.css` `@import` it and add only their own rules, so the front doors can't drift |
| `frontend/web/src/styles.css`, `theme.tsx` | The web app's import of the shared sheet, and the light/dark toggle as in `web-app/` |
| `frontend/mcp/web-app-url.ts` | `webAppUrl(path)`: the web app's address for an MCP UI's "Open in web app": `VITE_WEB_APP_URL` in production, the backend's `/__/frontend/web/` in dev |
| `scripts/screenshots.py` | As in `web-app/`, pointed at the backend's `/__/frontend/web` |

`frontend/vite.config.ts` and `build.mjs` already serve and build
`web/`. `tools/templates-smoke.sh` builds this template and runs its
backend scenario; it does not yet run browser scenarios against
`frontend/web/`.


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
