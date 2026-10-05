---
name: run
description: Run, stop, restart or reset an existing Reboot application locally. Detects whether the project is a Web App (`web/`), an MCP UI (`frontend/mcp/`) or both, makes sure dependencies and secrets are in place, then starts every process the app needs — the backend (`rbt dev run`), the frontend dev server, and, for MCP UIs only, a Cloudflare quick tunnel via the bundled `cloudflared` shim and the setup wizard (from which the user can launch MCPJam on demand). Also says how to stop the app completely (orphaned `main.py` and Envoy processes, the RocksDB LOCK), restart it, and reset dev state with `rbt dev expunge --yes`. Use this to bring an app back up, e.g. at the start of a new session, or when a restart or reset is needed.
argument-hint: [<project-directory>]
allowed-tools: Bash, Read, Write, Glob, Grep, Edit, AskUserQuestion
---

# run — Run a Reboot Application

> **Version notices:** if `rbt` reports a version mismatch or a newer
> Reboot, follow the [upgrade skill](../upgrade/SKILL.md).

The canonical procedure to start, stop, restart and reset an existing
Reboot app — typically at the start of a fresh session, when no
processes or exported environment survive. It **runs** an app; to
build one see the [`mcp-ui` skill](../mcp-ui/SKILL.md) and the
[web-app skill](../web-app/SKILL.md), which defer here to run.

## Step 1 — Locate the project

Use the directory the user named, or the current one. The project root
contains `.rbtrc`; if none is obvious, ask. Run every command below
from the project root.

## Step 2 — Detect the app type

| On disk | App type | Frontend dev server runs in |
| --- | --- | --- |
| `web/` only | **Web App** | `web/` |
| `frontend/mcp/` only | **MCP UI** | `frontend/` |
| `frontend/mcp/` and `frontend/web/` | **Both** (dual-frontend) | `frontend/` (one Vite server serves both) |
| `frontend/mcp/` and a top-level `web/` | **Both**, mid-migration | `frontend/` and `web/` (two Vite servers); finish the move into `frontend/web/` (build skill, "Adding the other front door") |

- An API using `mcp=Tool(` with no frontend directory is an MCP UI with
  no frontend (tools only, no `UI()` methods).
- Never use `mcp=None` as a signal: `mcp=` is required on every method.
- No match: ask "Is this an MCP UI, a standalone Web App, or both?" —
  don't guess; the type decides whether the tunnel and wizard start.

"MCP branch" below means MCP UI or Both.

## Step 3 — Dependencies

- Backend: no `.venv/` → `uv sync`. If `rbt dev run` warns `reboot[dev]`
  is not installed, add `reboot[dev]` at the same pin as `reboot` to the
  dev group of `pyproject.toml` (template in
  `../python/references/lifecycle-project-setup.md`) and `uv sync`; the
  tests and the dashboard's Features page run on it.
- Frontend: no `node_modules/` in a Step 2 frontend directory →
  `npm install` there.

## Step 4 — Secrets: the git-ignored env file

Apps read secrets from `os.environ`; `rbt dev run` loads them via
`--env-file`, set once in `.rbtrc`. Before starting the backend:

1. **Find required variables**: grep the backend for `os.environ[...]`,
   `os.environ.get(...)`, `os.getenv(...)`, and `main.py` for
   `Application(oauth=...)` provider credentials.
2. **`.rbtrc`** must contain `dev run --env-file=.env`; add it if not.
3. **Git-ignore `.env`** (it must never be committed): add `.env` to
   `.gitignore` (create it if needed) **before** writing any secret.
4. **Fill `.env`** with `KEY=VALUE` lines (e.g.
   `ANTHROPIC_API_KEY=sk-ant-...`). Ask the user for every required
   variable not already in `.env` or the environment. Never start with
   one missing — the app fails at boot or first use, illegibly.

**When `.env` changes:** `rbt dev run` watches its `--env-file` and
restarts with it re-read (1.6.0 source); shell-exported variables are
read once at start. One 1.6.0 project (client-portal) saw a changed
value ignored until a full restart, so if it doesn't show, stop and
start the backend (see "Stop, restart, reset"). Dev vs. Reboot Cloud
secrets: `python/references/lifecycle-secrets.md`.

## Step 5 — Start the processes

Run each process in its own background shell, from the project root.

### Before starting: is the port free?

The backend serves on `9991` unless `.rbtrc` has `dev run --port=<port>`.
Check both IP stacks:

```sh
lsof -nP -iTCP:9991 -sTCP:LISTEN
```

If held, inspect it (`ps -o pid,ppid,etime,command -p <pid>`):

- `envoy` or `backend/src/main.py` from this project with parent pid
  `1`: an orphan — clear it via "Stop, restart, reset" below.
- Anything else: not yours; don't kill it. Set `dev run --port=<port>`
  in `.rbtrc` instead. A flag `.rbtrc` sets can't also be passed on the
  command line (`the flag '--port' was set multiple times`; 1.6.0).

Check the frontend's Vite port the same way.

### Tunnel — MCP branch only

**Skip for a Web App**: it has no MCP clients, and a tunnel publishes
the dev server (and its `Development()` sign-in) on a public URL —
start one only if the user asks for a shareable preview.

For an MCP UI, before the backend, run the bundled `cloudflared` shim
in its own background shell so external MCP clients (e.g. ChatGPT) can
reach the dev server:

- `--url http://localhost:<BACKEND_PORT>` — `9991` or the
  `dev run --port=` value.
- `--metrics localhost:<METRICS_PORT>` — a free port (default `4040`).
  Once up, `http://localhost:<METRICS_PORT>/quicktunnel` returns the
  `*.trycloudflare.com` URL.

```sh
cloudflared tunnel \
    --metrics localhost:4040 \
    --url http://localhost:9991
```

### Backend — every app type

```sh
uv run rbt dev run --no-chaos
```

`--env-file=.env` (from `.rbtrc`) loads secrets; `--no-chaos` disables
the Chaos Monkey, which confuses a developer who can't see the backend
terminal.

### Frontend — every app type with a frontend

```sh
cd frontend && npm run dev   # MCP UI or dual-frontend
cd web && npm run dev        # standalone Web App
```

### Setup wizard — MCP branch only

An MCP UI's backend serves a **setup wizard** at its root
(`http://localhost:9991`) that walks the user through connecting an MCP
client (picking one, copying the `/mcp` endpoint, the OAuth handshake);
MCPJam is launched from it. Once the backend logs show it serving
traffic:

1. **Tell the user**, e.g. "Setup wizard (connect an MCP client) at
   http://localhost:9991".
2. **Open it once**, best-effort:

   ```sh
   "$BROWSER" http://localhost:9991 || xdg-open http://localhost:9991 || \
     python3 -m webbrowser http://localhost:9991
   ```

Open it **exactly once, at first startup — never on reloads**: under
`--watch` the backend reprints its "serving traffic" banner on every
hot reload, so don't add any reload-driven re-open.

**Skip for a Web App** (no wizard is served). Open it for every
MCP-branch app, including a **tools-only app** — the wizard is how the
user tries its tools in MCPJam or Claude.

### MCPJam inspector — MCP branch, on demand, never during startup

Never start MCPJam when bringing the app up. It is one of the wizard's
clients (with Claude and ChatGPT); when the user picks it, the wizard
shows the launch command for their own terminal:

```sh
npx @mcpjam/inspector@2.23.3 --url http://localhost:9991/mcp --oauth
```

Run it yourself only if the user asks, via the plugin's
`mcpjam-inspector` shim (pins the version; `--no-open` so you surface
the URL instead of popping a tab):

```sh
mcpjam-inspector --url http://localhost:9991/mcp --oauth
```

Either way it binds the fixed port 6274.

## Step 6 — Hand off

Confirm every process is up from its logs, then give the user:

- the app's inspect-page URL (`rbt inspect` reads the same state from
  the CLI — see the [inspect skill](../inspect/SKILL.md));
- MCP UI: the setup-wizard URL (`http://localhost:9991`, already open)
  and a first prompt (e.g. "Create a new todo list and show it to me").
  No MCPJam URL — it isn't running until picked in the wizard;
- Web App: the frontend dev-server URL and a first page to open;
- Both: all of the above.

> **Always start every process the app needs**: backend, frontend (if
> any), and for the MCP branch the tunnel (not MCPJam). The app is
> unusable until all are up.

## Stop, restart, reset

Killing `rbt dev run` (anything but SIGINT) leaves `main.py` and its
Envoy running, holding the port and state lock, serving stale data and
blocking the next start. Before stopping, restarting, expunging, or when
the app won't start, follow
[`references/stop-restart-reset.md`](references/stop-restart-reset.md);
never assume a stop worked.
