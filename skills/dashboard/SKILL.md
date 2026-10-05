---
name: dashboard
description: Start the Reboot developer dashboard (`rbt dashboard`) for a project and open it in the browser. Puts the minimum files in place (a `pyproject.toml` depending on `reboot[dev]`, a `.rbtrc`, the API directory), starts the dashboard in a background shell if one is not already serving, and opens its URL once. Use this while BUILDING an app — the dashboard watches the API directory from before anything is running, so the developer watches the API take shape as it is written. Not for running an app (see the run skill). `rbt dev run` does not start a dashboard: it only finds one already serving on `--dashboard-port` (default 9871), so start this one whenever the developer wants the dashboard, before or after the app runs.
argument-hint: [<project-directory>]
allowed-tools: Bash, Read, Write, Glob, Grep, Edit
---

# dashboard — Start the Reboot Developer Dashboard

> **Version notices:** if `rbt` reports a version mismatch or that a
> newer Reboot is available, the [upgrade skill](../upgrade/SKILL.md)
> says how and when to react.

The developer dashboard is a browser page, served by
`rbt dashboard`, that shows a Reboot application's API (the Models
page), its features as the `.feature` files under `tests/`
specify them (the Features page, with each feature's rules and
scenarios, the methods it uses, its `@wip` and `@blocked` marks, and
the recordings of its browser scenarios), and a changelog of how the
API has evolved. It reads the API and feature **files**, not a
running application, so it works from before the first API file is
written — which is exactly when to start it: bring the dashboard up
early in a build and the developer watches the API take shape while
you write it.

Use this skill when a build flow directs you here (the `mcp-ui`
and `web-app` skills do, right before the API is written) or when
the user asks for the dashboard while an app is being built.

> This skill **starts the dashboard**, nothing else. It does not run
> the application — that is the [run skill](../run/SKILL.md).
> `rbt dev run` does not start a dashboard; it only finds one
> already serving on its `--dashboard-port` (default 9871), so this
> skill is also how to get a dashboard next to a running app.
> The dashboard is optional: if any step below fails, tell the user
> the dashboard is not available and carry on with whatever you were
> building. Do not stop the build to debug it.

## Step 1 — Locate the project

Work in the directory the user named, or the current directory. The
project root is the directory holding (or about to hold) `.rbtrc`.
Every command below runs from the project root.

Decide where the API files live or will live. In every scaffold this
plugin produces that is `api/` at the project root; only deviate if
the project visibly keeps its API elsewhere (look for the
`generate <dir>` line in an existing `.rbtrc`).

## Step 2 — The minimum files

`rbt dashboard` needs three things on disk. In a build flow the
scaffolding step has already created all of them — check, and only
create what is missing:

1. **`pyproject.toml` depending on `reboot` and, in its dev group,
   `reboot[dev]`** (plus `.python-version`), so `uv run rbt`
   resolves. `rbt dashboard` refuses to start without the
   `reboot[dev]` extra, which carries what its Features page runs
   on; a project that pins only `reboot` gets `reboot[dev]` added at
   the same version. If missing, create both files following the
   templates in `../python/references/lifecycle-project-setup.md`.
2. **`.rbtrc`.** Everything the dashboard reads of the project comes
   from here: the API directory from the `generate <dir>` line, and,
   for its code checks, the application from `dev run --application=`
   and the generated Python from `generate --python=`. The file's
   location is also the project anchor (working directory and `.rbt/`
   state directory). Without a `generate <dir>` line, `rbt dashboard`
   refuses to start. If there is no `.rbtrc` yet, create a stub the
   later scaffolding will extend:

   ```
   generate api/
   generate --python=backend/api/
   dev run --application=backend/src/main.py
   ```

3. **The API directory** from Step 1 (`mkdir -p api`). It may be
   empty — the dashboard watches it and picks up files as they
   appear.

If `uv` is not on PATH (it always is under this plugin, whose `uv`
shim installs it on demand), install it first:

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Step 3 — Is a dashboard already serving?

The dashboard serves at `http://127.0.0.1:9871/`, which forwards to
wherever its page is. Probe it:

```sh
curl -sf -o /dev/null --max-time 2 http://127.0.0.1:9871/
```

If that succeeds, a dashboard is up — but check that it is **this
project's**. With two projects on one machine, 9871 belongs to
whichever dashboard started first, and nothing warns that you are
looking at the other project's API (student-sor, 1.5.0). Find the
dashboard processes and their working directories:

```sh
pgrep -fl "rbt dashboard"
lsof -a -d cwd -p <pid>
```

If one runs from this project root, surface the URL and stop. If
not, start this project's on another port with `--port=<port>`; a
later `rbt dev run` then needs `--dashboard-port=<port>` to find it.

If `pgrep` finds this project's `rbt dashboard` but the probe fails,
the dashboard has outlived its port (reboot-crm, 1.6.0): stop that
process and start a fresh one.

## Step 4 — Start the dashboard

From the project root, in its own background shell:

```sh
uv run rbt dashboard
```

It takes the API directory from the `generate <dir>` line in
`.rbtrc` (Step 2), spelled relative to the project root — that is how
file names are shown in the dashboard.

`rbt dashboard` takes only `--config`, `--default-config`,
`--working-directory` and `--port` (1.6.0). There is no flag to stop
it opening a browser: `rbt dev run --no-open-dashboard` makes one
easy to assume, but a guess such as `--no-open-browser` fails with
`unrecognized arguments` (exit 2), which in a background shell reads
as the dashboard failing to start.

It prints `Your dashboard is at http://127.0.0.1:9871/`
immediately and keeps running; wait until the probe from Step 3
succeeds before calling it up. It stays running for the life of the
session — leave it alone afterwards; it never needs a restart when
code changes, and `rbt dev run` coexists with it.

If it fails to come up (for example the local Envoy check fails
because neither Docker nor an `envoy` executable is available), warn
the user in one sentence and continue the build without it.

## Step 5 — Open it once

Open the URL in the browser, best-effort, exactly once:

```sh
"$BROWSER" http://127.0.0.1:9871/ || \
  xdg-open http://127.0.0.1:9871/ || \
  python3 -m webbrowser http://127.0.0.1:9871/
```

Once is enough for good: the page tracks its own viewers
(`Presence`) and the developer's preference about reopening, and
`rbt dev run` consults both before ever opening another. Never
re-open the page yourself on reloads or restarts.

Then tell the user the dashboard is up and what it is for — e.g.
"Developer dashboard (watch the API as I build it) at
http://127.0.0.1:9871/" — and get on with the build.

## Known issues

| Error / symptom | Meaning | Fix |
| --- | --- | --- |
| Call Graph shows `0 calls` and "Your application imports generated code that does not exist yet ... Run `rbt generate`" although the generated code exists; one orphaned `node .../langserver.index.js` per analysis | The dashboard's pyright child was orphaned and its shutdown hung (1.5.0). The 1.6.0 source starts pyright in its own process group and kills the group on shutdown, so this should not recur | `pkill -f langserver.index.js`; the graph then publishes |
| Same banner, status `CODE NOT CHECKED YET`, and the dashboard log shows `RuntimeError: pyright exited` / `WatchCode' failed with SystemAborted` | Pyright ran out of Node heap on a large generated tree; the banner blames the generated code wrongly (reboot-crm, 1.6.0) | Start with `NODE_OPTIONS="--max-old-space-size=12288" uv run rbt dashboard` |
| "code checked at" an old time, deleted methods still drawn, or "Your API files changed since the generated code was written" right after `rbt generate` | Stale analysis after a dashboard restart (reboot-crm, 1.6.0) | Run `uv run rbt generate` once more |
| Dashboard log keeps retrying an old app address (`WatchApi` ... `Connection refused`) after an expunge and restart | The dashboard's watch tasks outlived the app they watched (reboot-crm, 1.6.0) | Stop the dashboard, delete `.rbt/dashboard`, start it again |
| Probe on 9871 succeeds but the page shows another project's API | Port collision: another project's dashboard got 9871 first | Step 3: start this one with `--port=<port>` |
| Tab shows "live" off; a fresh `rbt dev run` finds no dashboard; `rbt dashboard` processes still running | The dashboard outlived its 9871 listener (reboot-crm, 1.6.0) | Stop it and start a fresh one |
| Next start fails with `cannot bind ... Address already in use` on 9871 | A killed dashboard left its Envoy holding the port (student-system, 1.5.0) | `lsof -t -iTCP:9871 -sTCP:LISTEN \| xargs kill`, after checking the holder (see the [run skill](../run/SKILL.md) § "Stop, restart, reset") |
| `rbt: error: unrecognized arguments` | A flag `rbt dashboard` does not take (e.g. `--no-open-browser`, `--api-directory`) | Use only the four flags in Step 4 |
