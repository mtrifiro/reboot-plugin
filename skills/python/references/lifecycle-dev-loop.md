---
title: Debug the Dev and Test Loop
impact: MEDIUM
impactDescription: A Reboot failure usually looks like a hang or a silent pass, and an agent that misreads one burns whole test runs chasing the wrong cause
tags: pytest, hang, faulthandler, exit-code, pipefail, retry, timeout, watch, dev-loop, debugging
summary: "Failures look like hangs or silent passes; `pytest -s`, stack dumps, exit codes; never test under the watcher."
step: any
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: ""
---

# Debug the Dev and Test Loop

## When you are here

A run has gone quiet, a suite reported unchecked success, or a test
passes alone but fails in the suite.
Stop/restart/expunge (kill order, ports, the RocksDB LOCK):
[`../../run/SKILL.md`](../../run/SKILL.md). The harness:
[`testing-harness.md`](testing-harness.md).

## Do this

**A hang is a retry loop**: Reboot retries a raising `initialize`
(forever, with backoff), a lock wait after 30 s, a presumed-deadlocked
transaction, a failed workflow attempt. Find the quiet failure:

1. **Rerun with `pytest -s`** — capture hides the runtime log, which
   holds the real exception and its retry line
   (`... failed with <Exception>; will retry after backoff ...`):

   ```bash
   uv run pytest -s tests/chain_test.py -k "sells a seat"
   ```

2. **If the log is silent, dump every thread's stack** at the wedge
   (or `kill -ABRT <pid>` on a run started with `PYTHONFAULTHANDLER=1`).
   An idle event loop means an await on something that never arrives;
   look upstream of the await:

   ```bash
   PYTHONFAULTHANDLER=1 timeout -s ABRT 300 uv run pytest -s tests/chain_test.py
   ```

3. **Bisect with a scratch test** booting servicers only, then
   `initialize`, then the failing call (found a hang four theory-driven
   changes missed; theater-network, 1.4.0).

4. **Trust only the exit code of the command you meant**, because
   without `pipefail`, `cmd | tail` reports `tail`'s exit (two false
   "suite passed" reports, theater-network, 1.4.0). Require a pytest
   summary line before calling a run green:

   ```bash
   set -o pipefail
   uv run pytest tests/ 2>&1 | tail -n 40   # exit is pytest's, not tail's
   ```

5. **Give every unattended run a timeout** (~2× measured runtime);
   report "timed out" apart from "no summary". Alive or idle:

   ```bash
   ps -o pid=,%cpu=,etime= -p $(pgrep -f "pytest tests/")
   ```

## Never

- **Calling a run with no summary line a pass.** Pytest has died
  mid-run with no summary, traceback or non-zero exit; one was reported
  "0 failed" with an `F` already in its dots (reboot-crm).
- **Running the suite while `rbt dev run` watches the same tree** — an
  edit regenerates `backend/api/**` under the suite, which then fails
  with `Method not found!` on methods that exist.
- **Iterating on a state shape while the watcher is live.** A
  hot-restart can persist a seconds-lived field type (even a typo), and
  the corrected code is refused as incompatible
  (`has switched type from ... waiting`) until you expunge. Write the API edit once in final
  form, or stop the watcher (theater-network, 1.4.0; the gate:
  [`api-schema-evolution.md`](api-schema-evolution.md)).
- **Counting log lines to measure progress** — effect-validation lines
  are rate-limited (Limits), so a long seed looks hung. Read actor state
  with `rbt inspect`.
- **Trusting a browser tab across a backend restart.** It retries dead
  subscriptions and stops receiving pushes; reload every tab after every
  restart or expunge.
- Saving a live-code edit in pieces: hot reload boots each save, and a
  reference to a constant the next save defines throws `NameError` in a
  scheduled chain until then (marquee-control, 1.4.1). One write per
  file, definitions before uses.

## Limits

- A failing `initialize` never fails the run; `Reboot().up()` never
  returns ([`lifecycle-initialize-hook.md`](lifecycle-initialize-hook.md)).
- A per-actor lock wait gives up after 30 s and is retried (1.6.0
  source); contention shows as repeated waits, not an error.
- Effect-validation warnings: one per method per 5 minutes (1.6.0 source).
- Parallel harness runs (`-n auto`, `-n4`), occasionally serial ones,
  have hung at zero CPU, silent, cause unknown (reboot-crm); only the
  step-5 timeout guards.

## Scales as

- A long-lived `rbt dev run --watch` session measured ~14% slower after
  12 reloads; a restart fully recovered it. Restart the backend and check
  `uptime` for ambient load before measuring (theater-chain, 1.4.1).

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `Application modified; restarting` | Dev watcher reloaded after a file change | Don't run the suite against a watched tree |
| `Not expecting stream to ever be done` (browser console) | Tab outlived its backend | Reload the tab |
| `Failed to flush monotonic clock high water mark: IO error: No such file or directory` | State expunged under a running app | Stop, then restart, per [`../../run/SKILL.md`](../../run/SKILL.md) |
| `has switched type from` | Watcher persisted a transient field type | Restore the persisted type, or expunge dev state |
| `protoc-gen-es-with-deps: spawnSync /bin/sh ENOBUFS`, then `protoc-gen-es: Plugin failed with status code 1`; `rbt dev run` waits for modification | The generated TypeScript passed Node's 1 MiB `execSync` buffer: the whole response, from about five state types | Patch `reboot/protoc_gen_es_with_deps.cjs` in the venv with `maxBuffer: 256 * 1024 * 1024` on `execSync(...)` (find the package with `pathlib.Path(list(reboot.__path__)[0])`: it may import as a namespace package); restart `rbt dev run`; `uv sync` undoes it |
| `NameError`, then `<Method>Aborted('Unknown')` and `retry after backoff`, in a live scheduled chain after a save | Hot reload applied one of two saves and booted the module half-edited; an undeclared error in a scheduled method retries with backoff | Write each file's edit once, definitions before uses; it heals on the next save |
| `docs.reboot.dev/develop/side_effects` in the effect-validation log, a 404 | A stale link in 1.4.1 | Read `https://docs.reboot.dev/learn_more/side_effects/` |

## See also

- [`../../run/SKILL.md`](../../run/SKILL.md): stop, restart, expunge
- [`testing-harness.md`](testing-harness.md): harness hangs and errors
- [`lifecycle-seeding.md`](lifecycle-seeding.md): slow seeds and effect validation
