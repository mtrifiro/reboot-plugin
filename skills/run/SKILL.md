---
name: run
description: Run, stop, restart or reset an existing Reboot application locally. Detects whether the project is a Web App (`web/`), an MCP UI (`frontend/mcp/`) or both, makes sure dependencies and secrets are in place, then starts every process the app needs — the backend (`rbt dev run`), the frontend dev server, and, for MCP UIs only, a Cloudflare quick tunnel via the bundled `cloudflared` shim and the setup wizard (from which the user can launch MCPJam on demand). Also says how to stop the app completely (orphaned `main.py` and Envoy processes, the RocksDB LOCK), restart it, and reset dev state with `rbt dev expunge --yes`. Use this to bring an app back up, e.g. at the start of a new session, or when a restart or reset is needed.
argument-hint: [<project-directory>]
allowed-tools: Bash, Read, Write, Glob, Grep, Edit, AskUserQuestion
---

# run — Run a Reboot Application

> **Version notices:** if `rbt` reports a version mismatch or that a
> newer Reboot is available, the [upgrade skill](../upgrade/SKILL.md)
> says how and when to react.

Bring an existing Reboot application up locally, and take it down
again. This skill is the single canonical "start the app" and "stop
the app" procedure: it figures out what kind of app the project is,
makes sure dependencies and secrets are ready, launches every process
the app needs, and says how to stop, restart and reset them.

Use it whenever the user wants to run, start, stop, restart, reset or
"bring up" an existing Reboot app — most commonly at the start of a
fresh session, where no processes and no exported environment survive
from last time.

> This skill **runs** an app; it does not build or modify one. To
> build, see the [`mcp-ui` skill](../mcp-ui/SKILL.md) and the
> [web-app skill](../web-app/SKILL.md) — those skills defer here for
> their "run the app" step.

## Step 1 — Locate the project

Work in the directory the user named, or the current directory. The project root is the directory that contains
`.rbtrc`. If there is no `.rbtrc` anywhere obvious, ask the user
where the app is. Every command below runs from the project root.

## Step 2 — Detect the app type

Decide from the frontend directories at the project root:

| On disk | App type | Frontend dev server runs in |
| --- | --- | --- |
| `web/` only | **Web App** | `web/` |
| `frontend/mcp/` only | **MCP UI** | `frontend/` |
| `frontend/mcp/` and `frontend/web/` | **Both** (dual-frontend) | `frontend/` (one Vite server serves both) |
| `frontend/mcp/` and a top-level `web/` | **Both** | `frontend/` and `web/` (two Vite servers) |

An MCP UI with no `UI()` methods (tools only) may have no
`frontend/mcp/` at all; treat an app whose API uses `mcp=Tool(` with
no frontend directory as an MCP UI with no frontend. Do **not** use
`mcp=None` as a signal: `mcp=` is a required keyword on every method,
so `mcp=None` appears in every app.

If none of these match, ask the user ("Is this an MCP UI, a
standalone Web App, or both?"). Do not guess — the app type decides
whether the tunnel and the setup wizard are started.

"MCP branch" below means MCP UI or Both.

## Step 3 — Dependencies

From the project root:

- Backend: if `.venv/` is missing, run `uv sync`. If `rbt dev run`
  later warns that `reboot[dev]` is not installed, add
  `reboot[dev]` at the same pin as `reboot` to the dev group of
  `pyproject.toml` (template in
  `../python/references/lifecycle-project-setup.md`) and `uv sync`
  again; the extra is what the tests and the dashboard's Features
  page run on.
- Frontend: if `node_modules/` is missing in a frontend directory
  from the Step 2 table, run `npm install` there.

## Step 4 — Secrets: the git-ignored env file

Reboot apps read secrets from `os.environ`. `rbt dev run` loads
them from an env file via its `--env-file` flag, configured once
in `.rbtrc`. Set this up **before** starting the backend:

1. **Find the required variables.** Grep the backend for
   `os.environ[...]`, `os.environ.get(...)`, and `os.getenv(...)`,
   and check `main.py` for `Application(oauth=...)` provider
   credentials. Every name found is a variable the app needs.
2. **Make sure `.rbtrc` references the env file.** It must contain
   the line `dev run --env-file=.env`. If it does not, add it.
3. **Make sure `.env` is git-ignored.** `.env` holds secrets and
   must never be committed. Check `.gitignore` at the project root
   for a line that ignores `.env`; if there is none, add `.env` to
   `.gitignore` (creating the file if it does not exist). Do this
   **before** writing any secret into `.env`.
4. **Fill `.env`.** Write standard `.env` `KEY=VALUE` lines — e.g.
   `ANTHROPIC_API_KEY=sk-ant-...`. For every required variable not
   already a line in `.env` (and not already exported in the
   environment), ask the user for the value and write it in.
   Never start the backend with a required
   variable missing — the app fails at boot or on first use, and
   the failure is hard to read.

**When `.env` changes.** In the 1.6.0 source, `rbt dev run` watches
its `--env-file` and restarts the application with the file re-read.
Variables exported in the shell are read once, when `rbt dev run`
starts. One project on 1.6.0 saw a changed `.env` value not take
effect until a full restart (client-portal), so if a changed value
does not show, stop and start the backend (see "Stop, restart,
reset").

The full secrets story — dev vs. Reboot Cloud — is in
`python/references/lifecycle-secrets.md`.

## Step 5 — Start the processes

Run each process in its own background shell, from the project
root.

### Before starting: is the port free?

The backend serves on `9991` unless `.rbtrc` has a
`dev run --port=<port>` line. Check that nothing holds it,
on either IP stack:

```sh
lsof -nP -iTCP:9991 -sTCP:LISTEN
```

If something does, look at it (`ps -o pid,ppid,etime,command -p <pid>`).
An `envoy` or `backend/src/main.py` from this project with parent
pid `1` is an orphan from an earlier run: clear it with "Stop,
restart, reset" below. Anything else belongs to someone else: do
not kill it; pick a free port instead, by setting
`dev run --port=<port>` in `.rbtrc`. A flag that `.rbtrc` sets cannot
also be passed on the command line (`the flag '--port' was set
multiple times`; 1.6.0). Check the frontend's Vite port the same way.

### Tunnel — MCP branch only

**Skip this for a Web App.** A Web App has no MCP clients, and a
tunnel would publish the local dev server (and its `Development()`
sign-in) on a public URL. Start one for a Web App only if the user
explicitly asks for a shareable preview.

For an MCP UI, before starting the backend, kick off a Cloudflare
quick tunnel pointed at the dev server's port so external MCP
clients (e.g. ChatGPT) can reach it. Run the bundled `cloudflared`
shim in its own background shell with two flags you choose:

- `--url http://localhost:<BACKEND_PORT>` — the dev server's HTTP
  port (`9991`, or the `dev run --port=` value).
- `--metrics localhost:<METRICS_PORT>` — a free local port for
  cloudflared's metrics endpoint (the default is `4040`; pick a
  different free port if `4040` is taken). Once the tunnel is up,
  `http://localhost:<METRICS_PORT>/quicktunnel` returns the
  allocated `*.trycloudflare.com` URL.

```sh
cloudflared tunnel \
    --metrics localhost:4040 \
    --url http://localhost:9991
```

### Backend — every app type

```sh
uv run rbt dev run --no-chaos
```

`--env-file=.env` in `.rbtrc` loads the secrets into the process;
`--no-chaos` disables the Chaos Monkey, a useful bug-finder that is
confusing to a developer who cannot see the backend terminal.

### Frontend — every app type with a frontend

Run the Vite dev server in each frontend directory from the Step 2
table:

```sh
cd frontend && npm run dev   # MCP UI or dual-frontend
cd web && npm run dev        # standalone Web App
```

### Setup wizard — MCP branch only

An MCP UI's backend serves an interactive **setup wizard** at
its root URL (`http://localhost:9991`) — a browser page that walks
the user through connecting the app to an MCP client (such as
MCPJam: picking a client, copying the `/mcp` endpoint, completing
the OAuth handshake). It is the natural starting point — and the
place the user launches MCPJam from, if they pick it — so open it.

Once the backend logs show it is serving traffic, do two things:

1. **Tell the user the wizard exists and what it's for** — e.g.
   "Setup wizard (connect an MCP client) at http://localhost:9991".
2. **Open it once in the browser**, best-effort:

   ```sh
   "$BROWSER" http://localhost:9991 || xdg-open http://localhost:9991 || \
     python3 -m webbrowser http://localhost:9991
   ```

Open the wizard **exactly once, at first startup — never on
reloads.** The backend runs under `--watch` and reprints its
"serving traffic" banner every time it hot-reloads on a code change;
re-opening a browser tab on each reload would be hostile. Because
you open it as a one-shot step during initial startup (not from a
loop that watches for the backend coming back up), this is naturally
satisfied — just don't add any reload-driven re-open.

**Skip this for a Web App.** A Web App has no MCP frontend, so no
wizard is served and there's nothing to connect — don't announce or
open it. Open it for every MCP-branch app, even a **tools-only app**
with no `UI()` methods: connecting MCPJam or Claude through the
wizard is exactly how the user tries those MCP tools out.

### MCPJam inspector — MCP branch, on demand, never during startup

Do **not** start the MCPJam inspector as part of bringing the app
up. MCPJam is just one of the MCP clients the setup wizard offers
(alongside Claude and ChatGPT), so starting it is only relevant
once the user picks **MCPJam** in the wizard. When they do, the
wizard's MCPJam step shows the exact launch command — pointed at
the app's `/mcp` endpoint with OAuth — for the user to run from
their own terminal:

```sh
npx @mcpjam/inspector@2.23.3 --url http://localhost:9991/mcp --oauth
```

Leave the launch to the wizard. Only run it yourself if the user
explicitly asks you to, and then use the plugin's
`mcpjam-inspector` shim (it pins the version and passes `--no-open`
so it does not pop a browser tab — you surface the URL instead):

```sh
mcpjam-inspector --url http://localhost:9991/mcp --oauth
```

Either way the inspector binds the fixed port 6274.

## Step 6 — Hand off

Confirm every process is up from its logs, then give the user:

- the application's own inspect-page URL (and that `rbt inspect`
  inspects the same state from the CLI — see the
  [inspect skill](../inspect/SKILL.md));
- for an MCP UI — the setup-wizard URL (`http://localhost:9991`,
  already opened for them, for connecting an MCP client) and a
  first prompt to try (e.g. "Create a new todo list and show it to
  me"). Don't hand over an MCPJam URL — MCPJam isn't running, and
  only starts if the user picks it in the wizard (see the on-demand
  step above);
- for a Web App — the frontend dev-server URL and a first page to
  open;
- for Both — all of the above.

> **Always start every process the app needs.** Every app type needs
> backend and frontend (when it has one), and the MCP branch also
> needs the tunnel. (MCPJam is not in this set — it is launched on
> demand from the wizard, only if the user picks it.) The app is not
> usable until all of them are up, so do not stop after one.

## Stop, restart, reset

Killing `rbt dev run` (anything but SIGINT) leaves the app's
`main.py` and its Envoy running: they hold the port and the state
lock, serve stale data, and block the next start. Before stopping,
restarting, expunging, or when the app won't start, read
[`references/stop-restart-reset.md`](references/stop-restart-reset.md)
and follow it; never assume a stop worked.

