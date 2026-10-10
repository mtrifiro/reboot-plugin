---
name: dashboard
description: Start the Reboot developer dashboard (`rbt dashboard`) for a project and open it once in the browser. Use while building, before the first API file, so the developer watches the API take shape, and whenever the user asks for the dashboard; not for running an app (the run skill). `rbt dev run` only finds a dashboard already serving on `--dashboard-port` (default 9871), so start it here, before or after the app runs.
argument-hint: [<project-directory>]
allowed-tools: Bash, Read, Write, Glob, Grep, Edit
---

# dashboard — Start the Reboot Developer Dashboard

> **Version notices:** if `rbt` reports a version mismatch or a newer
> Reboot, follow the [upgrade skill](../upgrade/SKILL.md).

`rbt dashboard` serves a browser page showing the app's API (Models
page), its features from the `.feature` files under `tests/` (Features
page: rules, scenarios, methods used, `@wip` and `@blocked` marks,
browser-scenario recordings), and an API changelog. It reads the API and
feature **files**, not a running app, so start it early in a build —
before the first API file — and the developer watches the API take
shape.

Come here when the [`build` skill](../build/SKILL.md) directs you
(before its Step 1, the API) or the user asks for the dashboard.

> This skill only **starts the dashboard**; running the app is the
> [run skill](../run/SKILL.md). `rbt dev run` doesn't start a
> dashboard — it only finds one already serving on `--dashboard-port`
> (default 9871) — so this is also how to get one next to a running
> app. The dashboard is optional: if any step fails, tell the user it's
> unavailable and carry on building; don't debug it.

## Step 1 — Locate the project

Use the directory the user named, or the current one. The project root
holds (or will hold) `.rbtrc`; run every command from it. The API
directory is `api/` in every scaffold this plugin produces, unless an
existing `.rbtrc`'s `generate <dir>` line says otherwise.

## Step 2 — The minimum files

In a build flow scaffolding has created these; create only what's
missing:

1. **`pyproject.toml` depending on `reboot` and, in its dev group,
   `reboot[dev]`** (plus `.python-version`), so `uv run rbt` resolves.
   `rbt dashboard` refuses to start without `reboot[dev]` (its Features
   page runs on it); add it at the same version as a `reboot`-only pin.
   Templates: `../python/references/lifecycle-project-setup.md`.
2. **`.rbtrc`** — the dashboard's only source: API directory from
   `generate <dir>` (required, or it refuses to start); for code checks,
   the app from `dev run --application=` and generated Python from
   `generate --python=`. Its location anchors the working directory and
   `.rbt/` state. If absent, create a stub scaffolding will extend:

   ```
   generate api/
   generate --python=backend/api/
   dev run --application=backend/src/main.py
   ```

   plus the dashboard's port, of this project's own so that projects on
   one machine don't meet: `<plugin>/skills/build/templates/copy.sh
   --ports <project>` prints `<backend> <dashboard> <vite>`; write
   `dashboard --port=<dashboard>` and `dev run --dashboard-port=<dashboard>`.
   The scaffold (build Step 2) keeps them.

3. **The API directory** (`mkdir -p api`); empty is fine — files are
   picked up as they appear.

If `uv` is not on PATH (this plugin's `uv` shim normally installs it):

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Step 3 — Is a dashboard already serving?

The dashboard serves on the port `.rbtrc` names (`dashboard --port=`;
9871 when it names none). Probe it:

```sh
curl -sf -o /dev/null --max-time 2 http://127.0.0.1:<port>/
```

If it answers, check it's **this project's**: a port belongs to whichever
dashboard started first, with no warning (student-sor, 1.5.0; two
sessions building one plan, findings-board, 1.6.0).

```sh
pgrep -fl "rbt dashboard"
lsof -a -d cwd -p <pid>
```

- One you started in this session runs from this project root:
  surface the URL and stop.
- One from this project root you didn't start (an earlier session's):
  the folder may have held another project since, whose API it still
  shows, and it doesn't re-read a replaced one (1.6.0). Stop it
  (`kill -INT <pid>`), start fresh (Step 4), then run
  `uv run rbt generate` once so it draws the calls (Known issues,
  "stale analysis").
- Otherwise start this project's with `--port=<port>`; a later
  `rbt dev run` then needs `--dashboard-port=<port>`.
- `pgrep` finds this project's but the probe fails: it outlived its port
  (reboot-crm, 1.6.0) — stop it and start fresh.

## Step 4 — Start the dashboard

From the project root, in its own background shell:

```sh
uv run rbt dashboard
```

- It reads the API directory from `.rbtrc`'s `generate <dir>`, relative
  to the project root (how file names are shown).
- Flags: only `--config`, `--default-config`, `--working-directory`,
  `--port` (1.6.0). No flag suppresses the browser
  (`rbt dev run --no-open-dashboard` exists, but `--no-open-browser`
  fails with `unrecognized arguments`, exit 2 — in a background shell
  that looks like a failed start).
- It prints `Your dashboard is at http://127.0.0.1:9871/` immediately;
  wait for the Step 3 probe to succeed before calling it up. Leave it
  running all session: no restart on code changes; `rbt dev run`
  coexists with it.
- If it fails (e.g. the local Envoy check finds neither Docker nor an
  `envoy` executable), warn in one sentence and continue without it.
- The plugin's `rbt` and `uv` shims give its pyright
  `NODE_OPTIONS=--max-old-space-size=12288` unless `NODE_OPTIONS` is
  set: on a mid-sized app the default heap runs out, the check retries
  forever and the Call Graph never publishes (reboot-crm, 1.6.0).

## Step 5 — Open it once

```sh
"$BROWSER" http://127.0.0.1:<port>/ || \
  xdg-open http://127.0.0.1:<port>/ || \
  python3 -m webbrowser http://127.0.0.1:<port>/
```

Once, for good: the page tracks its viewers (`Presence`) and the
developer's reopen preference, which `rbt dev run` consults. Never
re-open it on reloads or restarts. Tell the user, e.g. "Developer
dashboard (watch the API as I build it) at http://127.0.0.1:<port>/", and
continue the build.

## Known issues

| Error / symptom | Meaning | Fix |
| --- | --- | --- |
| Call Graph shows `0 calls` and "Your application imports generated code that does not exist yet ... Run `rbt generate`" although the generated code exists; one orphaned `node .../langserver.index.js` per analysis | Orphaned pyright child, hung shutdown (1.5.0); the 1.6.0 source kills pyright's process group on shutdown, so it should not recur | `pkill -f langserver.index.js`; the graph then publishes. The plugin's session-start report names such an orphan |
| Call Graph never publishes; the dashboard's Node sits at its heap limit, retrying | pyright out of Node's default heap on a mid-sized app (reboot-crm, 1.6.0) | The shims set `NODE_OPTIONS=--max-old-space-size=12288` for `rbt dashboard`; set a larger one yourself if it recurs |
| Same banner, status `CODE NOT CHECKED YET`, and the dashboard log shows `RuntimeError: pyright exited` / `WatchCode' failed with SystemAborted` | Pyright out of Node heap on a large generated tree; the banner wrongly blames generated code (reboot-crm, 1.6.0) | Start with `NODE_OPTIONS="--max-old-space-size=12288" uv run rbt dashboard` |
| "code checked at" an old time, deleted methods still drawn, or "Your API files changed since the generated code was written" right after `rbt generate` | Stale analysis after a dashboard restart (reboot-crm, 1.6.0) | Run `uv run rbt generate` once more |
| Dashboard log keeps retrying an old app address (`WatchApi` ... `Connection refused`) after an expunge and restart | Watch tasks outlived their app (reboot-crm, 1.6.0) | Stop the dashboard, delete `.rbt/dashboard`, restart it |
| Probe on 9871 succeeds but the page shows another project's API | Another project's dashboard got 9871 first | Step 3: start with `--port=<port>` |
| Models page shows types the project no longer has, no call lines, footer "API checked at" frozen at an earlier time | A dashboard from an earlier project in the same folder; the cwd check passes (1.6.0) | Step 3: stop it, start fresh, `uv run rbt generate` once |
| Tab shows "live" off; a fresh `rbt dev run` finds no dashboard; `rbt dashboard` processes still running | The dashboard outlived its 9871 listener (reboot-crm, 1.6.0) | Stop it and start a fresh one |
| Next start fails with `cannot bind ... Address already in use` on 9871 | A killed dashboard left its Envoy holding the port (student-system, 1.5.0) | `lsof -t -iTCP:9871 -sTCP:LISTEN \| xargs kill`, after checking the holder (see the [run skill](../run/SKILL.md) § "Stop, restart, reset") |
| `rbt: error: unrecognized arguments` | A flag `rbt dashboard` does not take (e.g. `--no-open-browser`, `--api-directory`) | Use only the four flags in Step 4 |
| Dashboard workers from earlier sessions, each at about 67% CPU, together over 1 GB | `rbt dashboard` outlives its session; SIGTERM to its backend leaves the worker and Envoy (reboot-crm, 1.6.0) | The session-start report names them; kill the group; `scripts/doctor.sh` lists this project's |
