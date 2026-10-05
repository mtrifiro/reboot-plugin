---
title: Project Shell — MCP UI Deltas
impact: CRITICAL
impactDescription: The shell files (`.rbtrc`, `pyproject.toml`, `.python-version`, `main.py`) wire the build, the dev server, the HMR routing, and the entry point — wrong shapes break either codegen or live reload before the app even boots.
tags: project, shell, rbtrc, pyproject, python-version, main, application-entry, hmr, dist, template
summary: "Copy `build/templates/mcp-ui/`: `.rbtrc` with `--default-config=hmr` and `:hmr`/`:dist` configs, no `--react-extensions`; `main.py` with `oauth=` and `example_prompts=`."
step: shell
applies: [mcp-ui]
always: false
verified: 1.6.0
docs: ""
---

# Project Shell — MCP UI Deltas

## When you are here

Creating an MCP UI's project-root files: `.python-version`,
`pyproject.toml`, `.rbtrc`, `.mypy.ini`, `pytest.ini`, `.gitignore`,
`backend/src/main.py`, `backend/src/example_prompts.py`. Shared shape
(layout, `.mypy.ini`, `.gitignore`, no `__init__.py`):
[`lifecycle-project-setup.md`](../../python/references/lifecycle-project-setup.md);
`.rbtrc` format:
[`lifecycle-rbtrc.md`](../../python/references/lifecycle-rbtrc.md);
`frontend/`: [`react-scaffolding.md`](react-scaffolding.md).

## Do this

Copy the template; do not retype these files
(placeholders: [`build/templates/README.md`](../../build/templates/README.md)):

```sh
<plugin>/skills/build/templates/copy.sh mcp-ui . <project> <app> "<Title>"
```

- **`.python-version`** — `3.12`; leave it.
- **`pyproject.toml`** — `reboot==1.6.0`, dev group `reboot[dev]==1.6.0`
  (tests and dashboard). Add a runtime dependency only when your code
  imports it (`httpx`, `uuid7`, …).
- **`.rbtrc`** — adds `dev run --default-config=hmr` and two configs:
  `dev run:hmr --frontend-host=http://localhost:4444` routes Envoy's
  `/__/frontend/**` to the Vite dev server (`cd frontend && npm run dev`);
  `dev run:dist --frontend-dist-path=frontend/dist` serves the built
  `frontend/dist/` (`rbt dev run --config=dist` after `npm run build`).
  `serve run` lines mirror `dev run` minus dev-only knobs (`--watch`,
  `--env-file`, the `:hmr`/`:dist` configs); Reboot Cloud runs
  `CMD ["rbt", "serve", "run"]`
  ([`lifecycle-dockerfile.md`](../../python/references/lifecycle-dockerfile.md)).
- **`backend/src/example_prompts.py`** — the `ExamplePrompt`s the
  root-page wizard offers; rewrite them for the app (below).
- **`backend/src/main.py`** — registers every servicer (`User` plus each
  application type), passes `example_prompts=`, and sets
  `oauth=OAuth(provider=OAuthProviderByEnvironment(dev=Development(),
  prod=None), allowed_origins=[])`. Set human-readable `title` and
  `description`; the wizard shows both (`title` defaults to the
  application name). No `initialize` hook is typical: the
  auto-constructed `User` covers per-user setup and `User`'s
  transactions create application instances.

### Example prompts

`ExamplePrompt` (from `reboot.application`) has `title` (the example's
identity; re-registering a `title` replaces it) and `prompts` (the user's
chat messages, one per turn). Each example is a **sequence** walking an
end-to-end flow through the app's tools (create → act → view). Write about
three covering the main user stories in a user's phrasing, most ending on
a "show me / open …" turn that renders a `UI()` (rule: `SKILL.md`,
"Example Prompts"). Worked set:
`public/reboot/examples/mcp-ui-counter/backend/src/example_prompts.py`.

### State is durable

`dev run --application-name=<project>` keys state that survives restarts;
`rbt dev expunge --application-name=<project>` resets it
(`lifecycle-rbtrc.md`).

## Never

- `dev run --default=hmr` — the flag is `--default-config=hmr`.
- `generate --react-extensions` in `.rbtrc` — Vite and `tsc`
  (`moduleResolution: "bundler"`) resolve `frontend/api/` without `.js`
  extensions. Needed only for a webpack/`ts-loader` bundler or a
  `--nodejs`/`--web` target sharing the React output directory (neither
  produced here); `rbt generate` rejects it alongside a future `--mobile`
  client (Metro cannot resolve `.js`-suffixed imports).
- `dev run --name=<project>` — deprecated alias of `--application-name`;
  warns on every start.
- Dropping `oauth=` from `main.py`: the `User` type is auto-constructed,
  and auto-construct servicers fail at startup without it.
- A `--watch` line for `api/`: `rbt dev run` already regenerates and
  restarts on API edits (`--generate-watch`, on by default at 1.6.0).

## Limits

- `prod=None` refuses to start under `rbt serve` / Reboot Cloud until a
  real provider is chosen ([`auth-oauth-providers.md`](auth-oauth-providers.md)).
- Omitting `allowed_origins` is a hard error in production; `[]` means
  same-origin only, right for backend-served UIs. A dual-frontend app
  lists its SPA's origin.
- `--env-file` is dev-only; production secrets use
  `rbt cloud secret set` (`lifecycle-secrets.md`).

## Scales as

Not measured.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `` `OAuth` requires `allowed_origins=[...]` to be set explicitly in production `` | `oauth=OAuth(...)` without `allowed_origins` outside `rbt dev run` (including the test harness) | Pass `allowed_origins=[]` (same-origin) or the SPA origins |
| `` WARNING: `--name` has been renamed to `--application-name` `` | Old `.rbtrc` flag | Use `--application-name` |

## See also

- [`react-scaffolding.md`](react-scaffolding.md) — the `frontend/` half
- [`lifecycle-project-setup.md`](../../python/references/lifecycle-project-setup.md) — shared layout and `.mypy.ini`
- [`build/templates/README.md`](../../build/templates/README.md) — every template file explained
