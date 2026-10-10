---
title: Stop, Restart and Reset a Local Reboot App
impact: HIGH
impactDescription: "`rbt dev run` leaves orphaned app and Envoy processes that hold the port and the state lock, serve stale data, and re-seed with old code"
tags: run, stop, restart, expunge, orphan, envoy, port, rocksdb, lock, dev
summary: "Killing `rbt dev run` orphans `main.py` and Envoy; stop in order and verify; expunge only after full stop."
step: run
applies: [mcp-ui, web-app, backend-only]
always: false
when: "you stop, restart or reset a running app, or it won't start"
verified: 1.6.0
docs: ""
---

# Stop, Restart and Reset a Local Reboot App

## When you are here

An app started with `rbt dev run` (see `../SKILL.md`) must stop,
restart or lose its dev state, or won't start because something from an
earlier run is alive.

`rbt dev run` is a supervisor: it starts
`python <project>/backend/src/main.py` (absolute path; one or more)
plus an `envoy` holding the app's port. In the 1.6.0 source it handles
SIGINT (Ctrl-C) by terminating every child's process group (read from
source, not yet confirmed in practice), has no SIGTERM handler, and
starts each child in its own session. So `kill`, `pkill` (SIGTERM) or
SIGKILL on `rbt dev run` or its `uv run` parent leave the app and Envoy
running with parent pid `1`. Observed 1.4.1–1.6.0 (reboot-crm,
cineloop, reboot-air, student-system, MattPRD): orphans serve reads
from a deleted store, hold the RocksDB lock, re-seed with old code and
block the port.

## Do this

### Stop completely

From the project root, in order:

```sh
# 1. The supervisor. SIGINT lets it reap its children.
pkill -INT -f "$PWD/.venv/bin/rbt dev run"

# 2. Application processes it left behind (path from
#    `dev run --application=` in .rbtrc).
pgrep -fl "$PWD/backend/src/main.py" && pkill -f "$PWD/backend/src/main.py"

# 3. Whatever still holds the port (an orphaned Envoy).
lsof -t -iTCP:9991 -sTCP:LISTEN | xargs kill

# 4. Verify: all three print nothing.
pgrep -fl "$PWD/backend/src/main.py"
lsof -nP -iTCP:9991 -sTCP:LISTEN
lsof .rbt/dev/<application-name>/p000000/LOCK
```

- Use the `dev run --port=` value if `.rbtrc` sets one; look at a port
  holder before killing it (see "Before starting").
- Stop the frontend, tunnel and dashboard by stopping their background
  shells. A killed `rbt dashboard` can leave an Envoy on `9871`
  (student-system, 1.5.0); clear it the same way.
- `scripts/doctor.sh`, in every scaffolded project, runs these checks
  in one command, says who serves each of the project's ports and from
  which directory, and names a test run in progress.

### Restart

1. Stop completely and wait until step 4 prints nothing — two
   `rbt dev run`s over one state directory fight over the RocksDB lock
   and crash-loop (theater-network, 1.4.0). The plugin's `rbt` shim waits
   up to 10 s for the lock to clear after a SIGINT and refuses a
   `dev run` while it is still held, naming the holder.
2. Start the backend again (Step 5).
3. Reload every open browser tab; a kept tab retries dead
   subscriptions.

A restart pauses work, not cancels it: workflows and scheduled tasks
resume from memoized steps (client-portal, 1.6.0). To stop recurring
work, use an application-level switch, or expunge.

### Reset dev state (expunge)

```sh
uv run rbt dev expunge --yes
```

- **Stop completely first.** It deletes only
  `.rbt/dev/<application-name>/` (1.6.0 source) and doesn't check for
  running processes: a live backend loops forever on
  `Failed to flush monotonic clock high water mark` (theater-chain,
  1.4.1); an orphan
  keeps or re-creates the state (reboot-air, 1.5.0).
- **Pass `--yes`.** Otherwise it asks for confirmation, and with no
  terminal waits forever (reboot-crm, 1.6.0); the plugin's `rbt` shim
  refuses the command instead, as it does while a process holds the
  state lock. `.rbtrc`'s `dev expunge --application-name=` line
  supplies the name.
- **Expect to sign in again**: it deletes the dev crypto root keys, so
  earlier OAuth tokens stop working (1.6.0 source).
- **Reload every open browser tab** once the backend is up; a kept tab
  mixes live data with frozen frames from the deleted state
  (theater-network, 1.4.0).
- **When to expunge:** dev state that lived through incompatible designs
  (changed method kinds, old scheduled tasks for reworked methods) fails
  with native asserts (`database.cc Check failed`) or context errors on
  task replay — expunge and reseed rather than debug (theater-network,
  1.4.0).

## Never

- **Iterating on a state shape with the `--watch` loop live** — the fix
  is refused until you expunge
  ([`lifecycle-dev-loop.md`](../../python/references/lifecycle-dev-loop.md) § Never).
- **If an edit does not take,** look for `Application modified;
  restarting` in the backend log; one `backend/src/` edit didn't
  restart the app (reboot-crm, 1.6.0). Restart by hand.
- **A second instance of the same app needs its own directory** with its
  own `.rbtrc` (different `--port`, `--application-name`), run with
  `uv run --project <repo> rbt dev run`. `.rbtrc` flags can't be
  overridden on the command line, and the venv's `rbt` run directly
  fails with `Failed to find 'protoc-gen-reboot_python'` (reboot-crm,
  1.6.0).
- **Assuming a stop worked.** Verify with step 4 of "Stop completely".

## Limits

- Only SIGINT lets `rbt dev run` clean up: no SIGTERM handler, each
  child in its own session (1.6.0 source).
- `.rbtrc` flags cannot be overridden on the command line.

## Scales as

- Not measured.

## Errors you will see

| Error / symptom | Meaning | Fix |
| --- | --- | --- |
| `cannot bind '0.0.0.0:9991': Address already in use`, then "This is a bug in the Envoy configuration Reboot generated ... report this bug" | Port already held, usually by an orphaned Envoy; not a Reboot bug | Stop completely, or set `dev run --port=<port>` in `.rbtrc` |
| `Failed to open rocksdb ... LOCK: Resource temporarily unavailable`, then `waiting for modification` | An orphaned `main.py` holds the state lock; no retry until a watched file changes | `lsof .rbt/dev/<application-name>/p000000/LOCK` names it; stop completely, start |
| `StatusCode.UNIMPLEMENTED ... Method not found!` from `validate_schema_backwards_compatibility` at boot | An older, incompatible process is alive (1.4.1) | Stop completely, start |
| Reads succeed, every write fails, after a restart or expunge | An orphan serves from a deleted store (1.6.0) | Stop completely, start |
| `curl localhost:<port>` returns another server's 404 | Another process holds the port on the other IP stack (`[::1]` vs `*`) | `lsof -nP -iTCP:<port> -sTCP:LISTEN`; use a free port |
| Every reader fails with `Unavailable: ping timeout` for about 10 minutes after each restart; Envoy at several hundred % CPU | Envoy's LuaJIT on macOS arm64 (reboot-crm, 1.6.0) | Wait it out; restart less; report upstream |
| Safari sign-in ends in `Missing pending-flow cookie` | Dev OAuth sets `Secure` cookies over http; WebKit drops them (1.6.0) | Chrome or Firefox locally, or TLS via `dev run --tls-certificate=... --tls-key=...` |
| `Failed to flush monotonic clock high water mark: IO error: No such file or directory` every second | State expunged under a running backend | Stop completely, start |

## See also

- [`../SKILL.md`](../SKILL.md) — starting every process the app needs
- [`../../python/references/lifecycle-dev-loop.md`](../../python/references/lifecycle-dev-loop.md) — test-loop hygiene, hangs
- [`../../python/references/lifecycle-rbtrc.md`](../../python/references/lifecycle-rbtrc.md) — `.rbtrc` flags, expunge line
