# Project templates

One minimal project per front door: every scaffold file verbatim, plus
the smallest API, servicer, `main.py`, feature file and test module that
build, type-check and pass one scenario. `tools/templates-smoke.sh`
builds both on every change. Copy a template, never retype a scaffold
file from memory or a reference, then replace the sample domain (a
counter) with the app's own.

## Copy

```sh
<plugin>/skills/build/templates/copy.sh <mcp-ui|web-app|both> <dest-dir> <project> <app> "<Title>"
# e.g.
<plugin>/skills/build/templates/copy.sh web-app . todo-list todo_list "Todo List"
# into a project that already has its API file and the dashboard's
# stubs (the build flow, Step 2):
<plugin>/skills/build/templates/copy.sh --merge web-app . todo-list todo_list "Todo List"
```

`<plugin>` is the plugin root (holding `bin/rbt`). `copy.sh` copies the
tree (dotfiles included), renames paths containing `__app__`, fills the
placeholders, and refuses a destination that already has an `.rbtrc`.
`--merge` instead keeps every file the destination already has, listing
each, except the dashboard's stub `.rbtrc`, `pyproject.toml` and
`.python-version`, which the template's replace. Either way it gives
the project a backend, dashboard and Vite port of its own, from a hash
of the project name and the next free set when one is held (a merge
keeps the ports the stub `.rbtrc` names), written into `.rbtrc`, the
Vite config, `.env.development` and `scripts/screenshots.py`;
`copy.sh --ports <project>` prints the set, for the dashboard skill.
It picks the project's accent from `palettes.json` by the same name
(`REBOOT_ACCENT=<name>` picks one) and writes it with the project's
`scripts/accent.py`. A merge keeps a stylesheet already there. In
a repository of its own it points `core.hooksPath` at `.githooks/`; in
no repository it starts one on `main` first. Then:

```sh
uv sync
rbt generate
(cd frontend && npm install)   # `cd web` for a web app
rbt generate                   # again: the React bindings need node_modules
```

`rbt` here is the plugin's shim. Inside a project with a `.venv/` it runs
that environment's `rbt`, so it and `uv run rbt` are one install (a
patch to one used to miss the other); it refuses `dev expunge` with no
`--yes` and no terminal, and `dev expunge` or a second `dev run` while a
process holds the state lock, naming the holder; it names `lib/` when the
plugin is installed without it; and it gives `rbt dashboard` the Node
heap its pyright needs.

`both` is the dual-frontend app: the `mcp-ui` template plus the SPA in
`frontend/web/` (see "`both/` adds" below).

## Placeholders

| Placeholder | Form | Example | Used in |
| --- | --- | --- | --- |
| `__project__` | kebab-case project name | `todo-list` | `pyproject.toml` `name`, `.rbtrc` `--application-name`, `package.json` `name` (`__project__-web`) |
| `__app__` | snake_case API package and module | `todo_list` | `api/__app__/v1/__app__.py`, `servicers/__app__.py`, `tests/__app___test.py`, imports (`__app__.v1.__app___rbt`), the `.mypy.ini` ignore stanza, the React import path |
| `__Title__` | human-readable title | `Todo List` | `Application(title=...)`, `<title>`, docstrings |
| `__Initial__` | the title's first letter, capitalized | `T` | the placeholder favicon in the web app's `index.html` |

| Beside the templates | What it is |
| --- | --- |
| `palettes.json` | The house palette: eight accents (teal, cyan, blue, indigo, violet, purple, plum, rose), each with every accent token for light and dark, held to WCAG contrast and off green, amber and red by `tests/templates/palettes_test.py`. The templates ship violet, `copy.sh` picks one per project, and each template's `scripts/accent.py` carries the same values |

A second API module needs its own `[mypy-<pkg>.v1.<name>_rbt]` stanza
in `.mypy.ini`.

## Files

Both front doors share the Python shell:

| File | What it is | Change when |
| --- | --- | --- |
| `.python-version` | `3.12`, the highest Python `rbt` supports | Never |
| `pyproject.toml` | `reboot==1.6.0` and the dev group (`reboot[dev]`, `mypy`, `pytest`, `pytest-timeout`, `types-protobuf`); no `[build-system]`, a virtual `uv` project | Adding a runtime dependency; browser scenarios add `playwright` and `pytest-playwright` (`python/references/testing-web-app.md`); an LLM agent turns `reboot` into `reboot[anthropic]` (`python/references/agent-pydantic-ai.md`) |
| `.rbtrc` | `rbt`'s config: codegen paths, watch globs, the app name, the env file, the project's ports, `serve run` | Config changes (`python/references/lifecycle-rbtrc.md`); a port only when a project still collides |
| `.mypy.ini` | Source roots on `mypy_path`, `explicit_package_bases`, one ignore stanza for the generated `_rbt` module | A new API module (one stanza each) |
| `pytest.ini` | `testpaths`, the `pythonpath` roots, `timeout = 300` so a hung scenario fails on its own, the `smoke` and `browser` markers | One `@<area>` marker per feature file, registered under `markers` |
| `.gitignore` | Dev state, generated code, env files, recordings, venv, `node_modules/`, frontend builds, `.reboot/`, `exports/` | Never; the generated-code paths match `.rbtrc` |
| `AGENTS.md` | The map for a coding agent: where each concept lives, how to run, test and deploy, the rules that cost most when broken | When a file moves, a command changes or a rule is learned; a new state type, front door or script adds its row |
| `CLAUDE.md` | `@AGENTS.md`, so Claude Code reads the same file as every other agent | Never; put everything in `AGENTS.md` |
| `FINDINGS.md` | The agent's log of surprises in a skill or the framework; the `report` skill files them upstream | Append items; never delete them |
| `api/__app__/v1/__app__.py` | Sample pydantic API | Always: the app's own types |
| `backend/src/servicers/__app__.py` | Sample servicers | Always |
| `backend/src/main.py` | `Application(...)` with `oauth=OAuth(provider=OAuthProviderByEnvironment(dev=Development(), prod=None), allowed_origins=[])` | Production provider and origins before deploy |
| `tests/counting.feature` | One `@wip` sample feature | Replace with the app's features (`feature` skill) |
| `tests/__app___test.py` | `application` fixture and `scenarios(...)` | Servicer list; one module per application configuration |
| `tests/run_progress.py`, `tests/conftest.py` | Records a test run's progress in `.reboot/test-run.json` for the Reboot band; `conftest.py` imports its hooks (`python/references/testing-project-setup.md`) | Never |
| `scripts/deploy.sh`, `scripts/api_removals.py` | A production deploy: a pushed commit, an additive API, `rbt cloud up`, the frontend built from the commit, a ledger line with the release record (`deploy` skill) | Never; settings go in `deploy/config` |
| `scripts/model_diff.py`, `tests/model_diff_test.py` | The model, authorizer and feature-file changes since the accepted design, each sorted Design or Prove by the flywheel's routing rule; the servicers without an authorizer; `--accept` records an acceptance | Never |
| `design/design.md`, `design/decisions.md`, `design/review.md`, `design/accepted.json` | Not in the template. `design.md` is written as the design is stated; `review.md`, `decisions.md` (one entry appended per acceptance) and `accepted.json` (`model_diff.py --accept`, a fingerprint of `api/` and the feature files) at "Accept the Design", committed together. That commit is the base every model diff measures from | `design.md` and `review.md` at each acceptance; `decisions.md` only appended |
| `.github/workflows/prove.yml`, `scripts/prove_comment.py` | Prove on every pull request: mypy, the full suite, one comment updated in place with the model diff and the scenario counts (`build/references/evidence.md`) | Never |
| `tests/last_run.py` | Records the last run in `tests/.last-run.json` with the tree's hash, for the pull request body, the release record and the pre-push gate; keeps `tests/.suite-running` while a run is on, for the suite guard | Never |
| `scripts/test.sh` | The suite in the size a change needs: `changed`, `smoke`, `backend`, `<area>`, `full` (the gate before a handoff or a push to `main`) | Never |
| `tests/feature_lint.py` | Fails a scenario before its first step when its feature says something reboot.bdd reads differently: a `Rule:` with no `Scenario:`, `with` clauses after the actor, a quoted saved value, a backtick in a quoted value; names the line and the fix | Never |
| `tests/harness_hygiene.py` | Settings a harness run needs on a developer's machine: test servers on `127.0.0.1`, the database on `[::1]`, a placeholder `ANTHROPIC_API_KEY` when `pydantic_ai` is installed | Never |
| `scripts/api_lint.py` | Before `rbt generate`: refuses, with the fix, what generate or the deploy would refuse later (reserved names, syntax past 3.10, quoted forward references, a Model from another package, `bytes` fields, field-less error Models); `prove.yml` runs it | Never |
| `scripts/placeholder.py` | While the app is down, a 503 page on the port the user visits (Vite's for a web app, else the backend's) naming the command that starts it; `rbt dev run` and `npm run dev` stop it, the `rbt` shim's watcher and the SessionStart hook start it; off under `REBOOT_NO_PLACEHOLDER=1` or `CI` | Never |
| `scripts/accent.py` | Lists the house palette with the current accent marked. `accent.py <name>` rewrites the accent tokens in `:root` and both dark blocks, the favicon and the placeholder page (stdlib, Python 3.9) | Never. Run it to change the accent (a marina gets teal). A brand edits the tokens instead |
| `scripts/doctor.sh` | Rules out the local causes that look like a framework flake: orphans, the state lock's holder, a run in progress, the allowlist variables, who serves each port | Never |
| `.githooks/pre-push` | Refuses a push to `main` of a tree the last full run did not pass on; `copy.sh` sets `core.hooksPath`, a clone runs `git config core.hooksPath .githooks` | Never |
| `tests/step_order.py` | Fails a scenario before its first step when it takes an action after a `Then`, naming the line and the fix (`feature` skill, Step 2) | Never |
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
| `frontend/mcp/styles.css` | The web app's tokens and classes (the house default) with system fonts (the `.ui` rule resets `--font-*`), shared by every UI (`mcp-ui/references/ui-design.md`) |
| `frontend/mcp/host-theme.ts` | `useHostTheme()`: applies the host's light/dark theme and follows changes |

### `web-app/` adds

| File | What it is |
| --- | --- |
| `web/package.json` | React 18, TypeScript 5.9, Vite 6, `zod` 4, the two Reboot packages pinned to the backend's `reboot`; `build` is `tsc -b && vite build`, `typecheck` is `tsc -b` (run it after an API rename; `tsc --noEmit` checks nothing)
| `web/vite.config.ts` | Stock config plus `resolve.dedupe`, `server.host: true`, the project's own port (`copy.sh` writes it), `strictPort: true`
| `web/tsconfig.json`, `tsconfig.app.json`, `tsconfig.node.json` | Split app and Vite-config projects; the app half includes `src/` and the generated client and type-checks cleanly at 1.6.0
| `web/.env.development` | `VITE_REBOOT_URL=http://localhost:<port>`, the backend port `.rbtrc` names (`copy.sh` writes both)
| `web/index.html`, `web/src/main.tsx` | Entry; the placeholder favicon (the title's initial on the accent; swap in the brand's mark); `RebootClientProvider`; the house default's typefaces from `@fontsource` (Bricolage Grotesque, Instrument Sans, JetBrains Mono; no CDN), then `styles.css`
| `web/src/styles.css` | The house default's tokens, light and dark, and the classes for the page anatomy, each primary view, detail and actions, listed at its top (`web-app/references/ui-design.md`)
| `web/src/App.tsx` | Sign-in gate on `useUser()`, one reader and one mutation, laid out in the page anatomy (title block with a lede, then a stat tile) |
| `web/src/nav.tsx` | `SiteNav`, the top bar's page links once there are two or more pages, stepping down to a ☰ menu as the width shrinks; `useBarHeight` keeps `--topbar-h` at the bar's real height (`ui-design.md`, 03)
| `web/src/contents.tsx` | `WithContents`, a long page's sections as a sidebar that stays in view, the one being read marked; a Contents panel below 640 px (`web-app/references/ui-design.md`, 03) |
| `web/src/theme.tsx` | `ThemeToggle` (light/dark, saved in `localStorage`, OS setting until chosen) and `applySavedTheme()`, called in `main.tsx` before render |
| `web/src/vite-env.d.ts` | Vite client types for `import.meta.env` |
| `tests/conftest.py` | The look steps, defined only when Playwright is installed (`python/references/testing-web-app.md`, "Look steps")
| `scripts/screenshots.py` | Signs in through the Development picker, waits for the skeletons to clear, saves every route at 1440 and 375 px, light and dark, to `screenshots/` (`ui-design.md`, 12)
| `scripts/page_timing.py` | Against a production build served locally, loads every route cold and warm and prints its worst content time, LCP and CLS; exits 1 over the thresholds (build Step 5) |

### `both/` adds

The `mcp-ui` template with a `list_counters` reader on `User` (so the
web app can find the user's counters) and the SPA beside the MCP UIs:

| File | What it is |
| --- | --- |
| `frontend/web/index.html`, `src/main.tsx`, `frontend/web/.env.development` | The SPA entry, with the placeholder favicon; served by the backend at `/__/frontend/web/`; `.env.development` names the backend's port so the address Vite prints can sign in too (plugin-browser, 1.6.0) |
| `frontend/web/src/App.tsx` | Sign-in gate, the user's counters as cards, `useCounter({ id })` per card; imports the one generated client via `@api/…` |
| `frontend/styles.css` | The one shared stylesheet (the same tokens and classes as `web-app/`); `web/src/styles.css` and `mcp/styles.css` `@import` it and add only their own rules, so the front doors can't drift |
| `frontend/web/src/styles.css`, `theme.tsx`, `nav.tsx`, `contents.tsx` | The web app's import of the shared sheet, the light/dark toggle and the page links as in `web-app/` |
| `frontend/mcp/web-app-url.ts` | `webAppUrl(path)`: the web app's address for an MCP UI's "Open in web app": `VITE_WEB_APP_URL` in production, the backend's `/__/frontend/web/` in dev |
| `scripts/screenshots.py`, `scripts/page_timing.py` | As in `web-app/`, pointed at the backend's `/__/frontend/web` |

`frontend/vite.config.ts` and `build.mjs` already serve and build
`web/`. `tools/templates-smoke.sh` builds this template and runs its
backend scenario; it does not yet run browser scenarios against
`frontend/web/`.


## Versions

Pinned to what the plugin ships: Reboot `1.6.0` (`bin/rbt`
`REBOOT_VERSION`) and the frontend set `@reboot-dev/create-ui@1.6.0`
writes, at the exact versions its ranges resolved to (`react`/`react-dom`
`18.3.1`, `typescript` `5.9.3`, `vite` `6.4.4`, `@vitejs/plugin-react`
`4.7.0`, `zod` `4.6.5`), not the React 19 / TypeScript 6 of
`npm create vite@latest`. Exact pins rather than lockfiles: a scaffold
builds the same way next month, and three `uv.lock`s would add 2 MB to
every install. `tools/templates-drift.py` keeps the three templates'
shared files identical; the `upgrade` skill bumps every `1.6.0` here
together.

## Smoke test

```sh
tools/templates-smoke.sh            # both front doors
SMOKE_FULL=1 tools/templates-smoke.sh web-app   # also run the scenario
```
