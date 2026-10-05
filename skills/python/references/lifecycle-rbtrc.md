---
title: Configure `.rbtrc` Correctly
impact: CRITICAL
impactDescription: `rbt generate` and `rbt dev run` won't find files without correct config
tags: rbtrc, config, generate, dev, expunge, application-name, port, watch
summary: "`.rbtrc` is line-based `<subcommand> <flag>`, not YAML; `--application-name` (not `--name`) persists state; `--env-file` for secrets; `serve run` lines for production; named configs."
step: shell
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: ""
---

# Configure `.rbtrc` Correctly

## When you are here

You are writing or fixing the project's `.rbtrc`, the per-project
config every `rbt` subcommand reads. Stopping, restarting and resetting
a running dev app (kill order, ports in use, the RocksDB LOCK) is the
[`run` skill](../../run/SKILL.md); secrets are
[`lifecycle-secrets.md`](lifecycle-secrets.md); the Dockerfile that
runs the `serve run` lines is
[`lifecycle-dockerfile.md`](lifecycle-dockerfile.md).

## Do this

`.rbtrc` is **line-based, not YAML**: each line is
`<subcommand> <flag>`, or `<subcommand>:<config> <flag>` for a named
config. Comments start with `#`. This matches the
[`reboot-bank-pydantic`](https://github.com/reboot-dev/reboot-bank-pydantic)
example:

```sh
# Find API definition files in 'api/'.
generate api/

# Tell `rbt` where to output its generated files.
generate --python=backend/api/
generate --react=web/src/api
generate --web=web/src/api

# Watch source files during `rbt dev run`. `api/` is the file you edit;
# `backend/api/` is regenerated from it.
dev run --watch=api/**/*.py
dev run --watch=backend/api/**/*.py
dev run --watch=backend/src/**/*.py

# Tell `rbt` that this is a Python application.
dev run --python

# Save state between `rbt dev run` restarts.
dev run --application-name=chat-room
dev expunge --application-name=chat-room

# Load secrets from a git-ignored env file.
dev run --env-file=.env

# Run the application!
dev run --application=backend/src/main.py
```

- **`--application-name=<name>`** keys the state that survives
  between `rbt dev run` restarts. Use the same value on
  `dev expunge`, so `rbt dev expunge --yes` resets exactly that state
  (stop the backend first; see Never). It is the canonical flag on
  `reboot>=1.0.4`; `--name` is a deprecated alias that warns.
- **`--env-file=<path>`** reads `KEY=VALUE` lines (`python-dotenv`
  syntax: `#` comments, blank lines, `export ` prefixes and quoted
  values all work) into the app's environment. `--env=KEY=VALUE`
  values override the file. A missing file is a warning, not an
  error. Editing the file while `rbt dev run` runs restarts the app
  (1.6.0 source), as editing a `--watch`ed file or `.rbtrc` itself
  does. Keep `.env` in `.gitignore`.
- **`--watch`** accepts globs and may repeat. With the default
  `--generate-watch`, `rbt dev run` also watches the `generate`
  directory itself and re-runs `rbt generate` (1.6.0 source); the
  explicit `api/**` line keeps reloads working under
  `--no-generate-watch`.
- **`--port=<n>`** moves the app off 9991, its default. Pin it here
  when another Reboot app on the machine already holds 9991.

### `serve run` lines: production config

`rbt serve run` (what the Cloud image's `CMD ["rbt", "serve", "run"]`
invokes, and any self-hosted `rbt serve`) reads the same file:

```sh
serve run --python
serve run --application=backend/src/main.py
serve run --application-name=<app>
serve run --tls=external
```

Use the same `--application-name` as the `dev run` lines.
[`lifecycle-dockerfile.md`](lifecycle-dockerfile.md) has the full
production block, including when `--tls=external` is right.

### Named configs

A `<subcommand>:<config>` line applies only when `--config=<config>`
is on the command line; `--default-config` picks one when none is:

```sh
# Default config (HMR / Vite).
dev run --default-config=hmr
dev run --frontend-root-path=frontend

dev run:hmr --frontend-host=http://localhost:4444

# Dist mode (no Vite).
dev run:dist --frontend-dist-path=frontend/dist
```

`rbt dev run` uses `hmr`; `rbt dev run --config=dist` switches.

## Never

- **YAML in `.rbtrc`** (`generate:` / `dev:` blocks with nested
  keys) — the file is one `<subcommand> <flag>` per line.
- **`dev run --name=<app>` in a fresh `.rbtrc`** — write
  `--application-name=<app>`. Fix an old `--name` line rather than
  ignoring the warning it prints on every run.
- **`rbt dev expunge` without `--yes` from a script or agent shell** —
  it asks for confirmation and, with no terminal, blocks forever
  instead of failing (reboot-crm, 1.6.0).
- **`rbt dev expunge` while `rbt dev run` is live** — the running
  server keeps its handle on the deleted RocksDB directory and loops
  on an IO error once per second, forever. Stop the backend, expunge,
  then start it again; the procedure is in the
  [`run` skill](../../run/SKILL.md).
- **Two `rbt dev run`s over one state directory** — they fight over
  the RocksDB LOCK and crash-loop. Kill the old process and wait
  before starting the next ([`run` skill](../../run/SKILL.md)).
- **Debugging dev state that lived through incompatible API changes**
  (changed method kinds, scheduled tasks pointing at reworked
  methods) — it trips native asserts and context-type errors on task
  replay. Expunge and reseed instead.
- **A literal secret on a `--env=KEY=secret` line** — `.rbtrc` is
  checked in. A `dev run --env-file=.env` line is fine; it is only a
  path.

## Limits

- **A flag set in `.rbtrc` cannot be overridden on the command
  line.** Passing it again is refused as a duplicate (1.6.0 source),
  for `--port`, `--application-name` and every other store-once flag.
- **A second dev instance of the same app needs its own directory**
  with its own `.rbtrc` (absolute paths work), started with
  `uv run --project <repo> rbt dev run`. Running the venv's `rbt`
  binary directly fails to find the `protoc-gen-reboot_python` plugin,
  which only `uv run` puts on `PATH` (reboot-crm, 1.6.0).
- **`--env-file` is `dev run` only** — not `rbt serve` or Reboot
  Cloud. Production secrets go through `rbt cloud secret set`
  ([`lifecycle-secrets.md`](lifecycle-secrets.md)).
- **An edit under `backend/src/` once failed to restart the app** with
  `dev run --watch=backend/src/**/*.py` set; a full restart picked it
  up. Not reproduced, cause unknown (reboot-crm, 1.6.0). If a fix
  "did not work", check the log for a restart before debugging the
  code.

## Scales as

- Not measured.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `the flag '--port' was set multiple times; it can only be set once, including in the `.rbtrc` file` | The flag is already set in `.rbtrc` (any flag name can appear here) | Edit `.rbtrc`, or run from a directory with its own `.rbtrc` |
| `'--name' has been renamed to '--application-name'. Please switch to using '--application-name'` | Deprecated alias in `.rbtrc` or on the command line | Rename the flag |
| `'--env-file' '.env' does not exist.` | Warning only; the app starts without those variables | Create the file, or ignore until the app needs secrets |
| `cannot bind '0.0.0.0:9991': Address already in use` (followed by "This is a bug in the Envoy configuration Reboot generated") | Another process, usually another Reboot app, holds the port; not a Reboot bug | `dev run --port=<other>` in `.rbtrc` |
| `Failed to find 'protoc-gen-reboot_python'. Please report this bug to the maintainers.` | `rbt` was run outside `uv run`, so the venv's `bin/` is not on `PATH` | `uv run rbt ...` (or `uv run --project <repo> rbt ...`) |
| `Failed to flush monotonic clock high water mark: IO error: No such file or directory` | State was expunged under a running app | Stop, expunge, restart ([`run` skill](../../run/SKILL.md)) |

## See also

- [`../../run/SKILL.md`](../../run/SKILL.md) — stop, restart, expunge procedure
- [`lifecycle-secrets.md`](lifecycle-secrets.md) — dev and Cloud secrets
- [`lifecycle-dockerfile.md`](lifecycle-dockerfile.md) — production `serve run` block
