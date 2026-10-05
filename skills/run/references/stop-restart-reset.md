---
title: Stop, Restart and Reset a Local Reboot App
impact: HIGH
impactDescription: "`rbt dev run` leaves orphaned app and Envoy processes that hold the port and the state lock, serve stale data, and re-seed with old code"
tags: run, stop, restart, expunge, orphan, envoy, port, rocksdb, lock, dev
summary: "Killing `rbt dev run` orphans `main.py` and Envoy; stop in order (SIGINT, app, port holder) and verify; `rbt dev expunge --yes` only after a full stop; reload tabs."
step: run
applies: [mcp-ui, web-app, backend-only]
always: false
when: "you stop, restart or reset a running app, or it won't start"
verified: 1.6.0
docs: ""
---

# Stop, Restart and Reset a Local Reboot App

## When you are here

An app started with `rbt dev run` (see `../SKILL.md`) has to stop,
restart, or lose its dev state, or it refuses to start because
something from an earlier run is still alive. Starting the app is in
`../SKILL.md`.

`rbt dev run` is a supervisor. It starts the application
as `python <project>/backend/src/main.py` (absolute path, 1.6.0
source; one or more processes) plus an `envoy` proxy that holds the
app's port. In the 1.6.0 source the CLI handles SIGINT (Ctrl-C) by
running its cleanup, which terminates every child's process group
(read from the source, not yet confirmed in practice). It has no
SIGTERM handler, and it starts each child in a session of its own.
So `kill`, `pkill` (both SIGTERM) or SIGKILL on `rbt dev run` or its
`uv run` parent leave the application and its Envoy running, with
parent pid `1`. Observed from 1.4.1 to 1.6.0 (reboot-crm, cineloop,
reboot-air, student-system, MattPRD): orphans keep serving reads
from a deleted store, hold the RocksDB lock, re-seed with old code,
and block the port. Never assume a stop worked; verify it.

## Do this

### Stop completely

From the project root, in this order:

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

Use the project's port if `.rbtrc` sets `dev run --port=`, and look
at a port holder before killing it (see "Before starting"). Stop
the frontend, tunnel and dashboard by stopping their background
shells. A killed `rbt dashboard` can leave an Envoy on `9871` too
(student-system, 1.5.0); clear it the same way.

### Restart

1. Stop completely (above) and wait until step 4 prints nothing.
   Two `rbt dev run`s over one state directory fight over the
   RocksDB lock and crash-loop (theater-network, 1.4.0).
2. Start the backend again (Step 5).
3. Reload every open browser tab. A tab kept across a restart keeps
   retrying dead subscriptions.

A restart pauses work; it does not cancel it. Workflows and
scheduled tasks resume from their memoized steps on the next start
(client-portal, 1.6.0). To really stop recurring work, use an
application-level switch, or expunge.

### Reset dev state (expunge)

```sh
uv run rbt dev expunge --yes
```

- **Stop completely first.** `rbt dev expunge` deletes
  `.rbt/dev/<application-name>/` and nothing else (1.6.0 source). It
  does not check for running processes: a live backend then loops
  forever on `Failed to flush monotonic clock high water mark`
  (theater-chain, 1.4.1), and an orphan keeps or re-creates the
  state (reboot-air, 1.5.0).
- **Pass `--yes`.** Without it the command asks for confirmation,
  and from a shell with no terminal it waits forever (reboot-crm,
  1.6.0). `.rbtrc`'s `dev expunge --application-name=` line supplies
  the name.
- **Expect to sign in again.** The expunge also deletes the dev
  crypto root keys, so OAuth tokens minted before it stop working
  (1.6.0 source).
- **Reload every open browser tab** after the backend is back up.
  A tab kept across an expunge mixes live data with frozen frames
  from the deleted state (theater-network, 1.4.0).
- **When to expunge:** dev state that lived through incompatible
  designs (changed method kinds, old scheduled tasks for reworked
  methods) fails with native asserts (`database.cc Check failed`)
  or context errors on task replay. Expunge and reseed rather than
  debugging it (theater-network, 1.4.0).

## Never

- **Iterating on a state shape with the `--watch` loop live.** A
  hot restart persists whatever schema booted, even a typo that lived
  for seconds, and the corrected code is then refused (`has switched
  type from ... waiting`) until you expunge (theater-network, 1.4.0).
  Or write the API edit once, in its final form.
- **If an edit does not take,** check for an `Application modified;
  restarting` line in the backend log. One project saw a
  `backend/src/` edit not restart the app (reboot-crm, 1.6.0).
  Restart by hand.
- **A second instance of the same app needs its own directory** with
  its own `.rbtrc` (different `--port`, `--application-name`), run
  with `uv run --project <repo> rbt dev run`. `.rbtrc` flags cannot
  be overridden on the command line, and the venv's `rbt` run
  directly fails with `Failed to find 'protoc-gen-reboot_python'`
  (reboot-crm, 1.6.0).
- **Assuming a stop worked.** Verify with step 4 of "Stop completely".

## Limits

- `rbt dev run` has no SIGTERM handler and starts each child in its
  own session, so only SIGINT gives it a chance to clean up (1.6.0
  source).
- `.rbtrc` flags cannot be overridden on the command line.

## Scales as

- Not measured.

## Errors you will see

| Error / symptom | Meaning | Fix |
| --- | --- | --- |
| `cannot bind '0.0.0.0:9991': Address already in use`, then "This is a bug in the Envoy configuration Reboot generated ... report this bug" | Something already holds the port, usually an orphaned Envoy. Not a Reboot bug | Stop completely, or set `dev run --port=<port>` in `.rbtrc` |
| `Failed to open rocksdb ... LOCK: Resource temporarily unavailable`, then `waiting for modification` | An orphaned `main.py` holds the state lock. `rbt dev run` does not retry until a watched file changes | `lsof .rbt/dev/<application-name>/p000000/LOCK` names the holder; stop completely, then start again |
| `StatusCode.UNIMPLEMENTED ... Method not found!` from `validate_schema_backwards_compatibility` at boot | An older, incompatible process of the app is still alive (1.4.1) | Stop completely, then start |
| Reads succeed, every write fails, after a restart or expunge | An orphan is serving from a deleted store (1.6.0) | Stop completely, then start |
| `curl localhost:<port>` returns another server's 404 | Another process holds the port on the other IP stack (`[::1]` vs `*`) | `lsof -nP -iTCP:<port> -sTCP:LISTEN`; move to a free port |
| Every reader fails with `Unavailable: ping timeout` for about 10 minutes after each restart; Envoy at several hundred % CPU | Envoy's LuaJIT on macOS arm64 (reboot-crm, 1.6.0) | Wait for the window to pass; restart less often; report it upstream |
| Safari sign-in ends in `Missing pending-flow cookie` | The dev OAuth server sets `Secure` cookies over plain http, and WebKit drops them (1.6.0) | Use Chrome or Firefox locally, or serve the backend over TLS with `dev run --tls-certificate=... --tls-key=...` |
| `Failed to flush monotonic clock high water mark: IO error: No such file or directory` every second | State was expunged under a running backend | Stop completely, then start |

## See also

- [`../SKILL.md`](../SKILL.md) — starting every process the app needs
- [`../../python/references/lifecycle-dev-loop.md`](../../python/references/lifecycle-dev-loop.md) — test-loop hygiene, hangs
- [`../../python/references/lifecycle-rbtrc.md`](../../python/references/lifecycle-rbtrc.md) — `.rbtrc` flags, expunge line
