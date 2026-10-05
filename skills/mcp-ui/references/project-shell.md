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

You are creating the project-root files of an MCP UI: `.python-version`,
`pyproject.toml`, `.rbtrc`, `.mypy.ini`, `pytest.ini`, `.gitignore`,
`backend/src/main.py` and `backend/src/example_prompts.py`. The shape
shared with every Reboot project (layout, `.mypy.ini`, `.gitignore`,
no `__init__.py`) is
[`lifecycle-project-setup.md`](../../python/references/lifecycle-project-setup.md);
the `.rbtrc` format is
[`lifecycle-rbtrc.md`](../../python/references/lifecycle-rbtrc.md).
The `frontend/` tree is [`react-scaffolding.md`](react-scaffolding.md).

## Do this

Copy the template; do not retype these files:

```sh
<plugin>/skills/build/templates/copy.sh mcp-ui . <project> <app> "<Title>"
```

([`build/templates/README.md`](../../build/templates/README.md) has the
placeholders.) What each MCP-UI-specific file is for, and what to change:

- **`.python-version`** — `3.12`. Leave it.
- **`pyproject.toml`** — `reboot==1.6.0`, dev group `reboot[dev]==1.6.0`
  (what the tests and the dashboard run on). Add a runtime dependency
  only when your code imports it (`httpx`, `uuid7`, …); `reboot`
  needs none.
- **`.rbtrc`** — beyond the shared shape it adds
  `dev run --default-config=hmr` plus two named configs:
  `dev run:hmr --frontend-host=http://localhost:4444` routes Envoy's
  `/__/frontend/**` to the Vite dev server (`cd frontend && npm run dev`),
  and `dev run:dist --frontend-dist-path=frontend/dist` serves the
  built `frontend/dist/` instead (`rbt dev run --config=dist`, after
  `npm run build`). Its `serve run` lines mirror `dev run` minus the
  dev-only knobs (`--watch`, `--env-file`, the `:hmr`/`:dist` configs);
  Reboot Cloud runs `CMD ["rbt", "serve", "run"]`
  ([`lifecycle-dockerfile.md`](../../python/references/lifecycle-dockerfile.md)).
- **`backend/src/example_prompts.py`** — the `ExamplePrompt`s the
  root-page wizard offers. Rewrite them for the app (rules below).
- **`backend/src/main.py`** — registers every servicer (`User` plus each
  application type), passes `example_prompts=`, and sets
  `oauth=OAuth(provider=OAuthProviderByEnvironment(dev=Development(),
  prod=None), allowed_origins=[])`. Set `title` and `description` to
  something human-readable: the wizard shows both (`title` defaults
  to the application name). A typical MCP UI has no `initialize`
  hook: the auto-constructed `User` covers per-user setup, and
  application-type instances are created by `User`'s transactions.

### Example prompts

`ExamplePrompt` (from `reboot.application`) has two fields: `title`, a
short label that is the example's identity (re-registering the same
`title` replaces the entry), and `prompts`, the chat messages the user
sends, one per turn. One example is a **sequence** walking an
end-to-end flow through the app's tools (create → act → view), not
one isolated message. Write about three that together exercise the
main user stories, phrased the way a user talks, and end most of them
on a "show me / open …" turn that renders a `UI()` component (rule in
`SKILL.md`, "Example Prompts"). Worked set:
`public/reboot/examples/mcp-ui-counter/backend/src/example_prompts.py`.

### State is durable

`dev run --application-name=<project>` keys the state that survives
restarts; `rbt dev expunge --application-name=<project>` resets it
(details in `lifecycle-rbtrc.md`).

## Never

- `dev run --default=hmr` — the flag is `--default-config=hmr`.
- `generate --react-extensions` in `.rbtrc`. The React client is
  generated into `frontend/api/` and resolved by Vite and by `tsc`
  under `moduleResolution: "bundler"` without `.js` extensions, so the
  flag buys nothing. It is needed only for a webpack/`ts-loader`
  bundler or a `--nodejs`/`--web` target sharing the React output
  directory, neither of which this skill produces, and `rbt generate`
  rejects it alongside a future `--mobile` client (Metro cannot
  resolve the `.js`-suffixed imports).
- `dev run --name=<project>` — deprecated alias of
  `--application-name`, warns on every start.
- Dropping `oauth=` from `main.py`: the `User` type is
  auto-constructed, and auto-construct servicers make the application
  fail at startup without it.
- A `--watch` line for `api/`: `rbt dev run` already regenerates and
  restarts on API edits (`--generate-watch`, on by default at 1.6.0).

## Limits

- `prod=None` refuses to start under `rbt serve` / Reboot Cloud until
  a real provider is chosen ([`auth-oauth-providers.md`](auth-oauth-providers.md)).
- Leaving `allowed_origins` out entirely is a hard error in production;
  `[]` means same-origin only, which is right for UIs served by the
  backend. A dual-frontend app lists its web SPA's origin.
- `--env-file` is dev-only; production secrets go through
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
