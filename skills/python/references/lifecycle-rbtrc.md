---
title: Configure `.rbtrc` Correctly
impact: CRITICAL
impactDescription: `rbt generate` and `rbt dev run` won't find files without correct config
tags: rbtrc, config, generate, dev, expunge, application-name, port, watch
summary: "`.rbtrc` is line-based, not YAML; `--application-name` not `--name`; `--env-file` for secrets; `serve run` lines; named configs."
step: shell
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: ""
---

# Configure `.rbtrc` Correctly

## When you are here

Writing or fixing `.rbtrc`, the per-project config every `rbt`
subcommand reads. Stop/restart/reset a dev app (kill order, ports, the
RocksDB LOCK): [`run` skill](../../run/SKILL.md); secrets:
[`lifecycle-secrets.md`](lifecycle-secrets.md); the Dockerfile running
`serve run`: [`lifecycle-dockerfile.md`](lifecycle-dockerfile.md).

## Do this

`.rbtrc` is **line-based, not YAML**: one `<subcommand> <flag>` per
line, or `<subcommand>:<config> <flag>` for a named config; `#`
comments. From
[`reboot-bank-pydantic`](https://github.com/reboot-dev/reboot-bank-pydantic):

```sh
generate api/
generate --python=backend/api/
generate --react=web/src/api
generate --web=web/src/api

# `api/` is what you edit; `backend/api/` is regenerated from it.
dev run --watch=api/**/*.py
dev run --watch=backend/api/**/*.py
dev run --watch=backend/src/**/*.py

dev run --python

# Save state between `rbt dev run` restarts.
dev run --application-name=chat-room
dev expunge --application-name=chat-room

# Secrets from a git-ignored env file.
dev run --env-file=.env

dev run --application=backend/src/main.py
```

- **`--application-name=<name>`** keys state surviving restarts; the
  same value on `dev expunge` makes `rbt dev expunge --yes` reset exactly
  that state. Canonical on `reboot>=1.0.4`; `--name` is a deprecated
  alias that warns.
- **`--env-file=<path>`** loads `KEY=VALUE` lines (`python-dotenv`
  syntax: `#` comments, blank lines, `export ` prefixes, quoted values)
  into the app's environment; `--env=KEY=VALUE` overrides the file. A
  missing file is a warning. Editing it while `rbt dev run` runs
  restarts the app (1.6.0 source), like a `--watch`ed file or `.rbtrc`.
  Keep `.env` in `.gitignore`.
- **`--watch`**: repeatable globs. The default `--generate-watch` also
  watches the `generate` directory and re-runs `rbt generate` (1.6.0
  source); the explicit `api/**` line keeps reloads under
  `--no-generate-watch`.
- **`--port=<n>`**: off the default 9991, when another Reboot app holds it.

### `serve run` lines: production config

`rbt serve run` (Cloud image `CMD ["rbt", "serve", "run"]` or
self-hosted) reads the same file; same `--application-name` as
`dev run`. Full block: [`lifecycle-dockerfile.md`](lifecycle-dockerfile.md).

```sh
serve run --python
serve run --application=backend/src/main.py
serve run --application-name=<app>
serve run --tls=external
```

### Named configs

A `<subcommand>:<config>` line applies only with `--config=<config>`;
`--default-config` picks one when none is given. Below, `rbt dev run`
uses `hmr`; `rbt dev run --config=dist` switches:

```sh
# Default config (HMR / Vite).
dev run --default-config=hmr
dev run --frontend-root-path=frontend

dev run:hmr --frontend-host=http://localhost:4444

# Dist mode (no Vite).
dev run:dist --frontend-dist-path=frontend/dist
```

## Never

- **YAML in `.rbtrc`** (`generate:` / `dev:` blocks with nested keys).
- **`dev run --name=<app>`** — write `--application-name=<app>`; fix
  old `--name` lines rather than living with the warning.
- **`rbt dev expunge` without `--yes` from a script or agent shell** —
  with no terminal its confirmation prompt blocks forever (reboot-crm,
  1.6.0).
- **`rbt dev expunge` while `rbt dev run` is live** — the server holds
  the deleted RocksDB directory and loops on an IO error every second.
  Stop, expunge, start ([`run` skill](../../run/SKILL.md)).
- **Two `rbt dev run`s over one state directory** — they crash-loop on
  the RocksDB LOCK; kill the old one and wait.
- **Debugging dev state that lived through incompatible API changes**
  (changed method kinds, tasks pointing at reworked methods) — native
  asserts and context-type errors on task replay. Stop the app,
  `rbt dev expunge --application-name=<name> --yes`, reseed, reload open
  tabs (theater-network, 1.4.0).
- **A literal secret on a `--env=KEY=secret` line** — `.rbtrc` is
  checked in. `dev run --env-file=.env` is fine; it's only a path.

## Limits

- **A flag set in `.rbtrc` can't be overridden on the command line**;
  passing it again is refused as a duplicate (1.6.0 source), for
  `--port`, `--application-name` and every other store-once flag.
- **A second dev instance of the same app needs its own directory** and
  `.rbtrc` (absolute paths work), started with
  `uv run --project <repo> rbt dev run`. The venv's `rbt` run directly
  can't find `protoc-gen-reboot_python`, which only `uv run` puts on
  `PATH` (reboot-crm, 1.6.0).
- **`--env-file` is `dev run` only** — not `rbt serve` or Reboot Cloud;
  production secrets use `rbt cloud secret set`
  ([`lifecycle-secrets.md`](lifecycle-secrets.md)).
- **A `backend/src/` edit once didn't restart the app** despite
  `dev run --watch=backend/src/**/*.py` (not reproduced, cause unknown;
  reboot-crm, 1.6.0). If a fix "did not work", check the log for a
  restart first.

## Scales as

- Not measured.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `the flag '--port' was set multiple times; it can only be set once, including in the `.rbtrc` file` | Flag already set in `.rbtrc` (any flag name can appear) | Edit `.rbtrc`, or run from a directory with its own `.rbtrc` |
| `'--name' has been renamed to '--application-name'. Please switch to using '--application-name'` | Deprecated alias in `.rbtrc` or on the command line | Rename the flag |
| `'--env-file' '.env' does not exist.` | Warning only; app starts without those variables | Create the file, or ignore until secrets are needed |
| `cannot bind '0.0.0.0:9991': Address already in use` (followed by "This is a bug in the Envoy configuration Reboot generated") | Another process, usually another Reboot app, holds the port; not a Reboot bug | `dev run --port=<other>` in `.rbtrc` |
| `Failed to find 'protoc-gen-reboot_python'. Please report this bug to the maintainers.` | `rbt` run outside `uv run`; venv `bin/` not on `PATH` | `uv run rbt ...` (or `uv run --project <repo> rbt ...`) |

## See also

- [`../../run/SKILL.md`](../../run/SKILL.md) — stop, restart, expunge procedure
- [`lifecycle-secrets.md`](lifecycle-secrets.md) — dev and Cloud secrets
- [`lifecycle-dockerfile.md`](lifecycle-dockerfile.md) — production `serve run` block
