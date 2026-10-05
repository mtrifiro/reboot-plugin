---
title: Debug the Dev and Test Loop
impact: MEDIUM
impactDescription: A Reboot failure usually looks like a hang or a silent pass, and an agent that misreads one burns whole test runs chasing the wrong cause
tags: pytest, hang, faulthandler, exit-code, pipefail, retry, timeout, watch, dev-loop, debugging
summary: "A Reboot failure looks like a hang (a retry loop) or a silent pass: rerun with `pytest -s`, dump stacks, bisect, trust only exit codes, never test under the watcher."
step: any
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: ""
---

# Debug the Dev and Test Loop

## When you are here

A test run or `rbt dev run` has gone quiet, a suite reported success
you have not checked, or the same test passes alone and fails in the
suite. This file is the discipline for finding out what is actually
happening. Stopping, restarting and expunging a dev app (kill order,
ports, the RocksDB LOCK) are covered in
[`../../run/SKILL.md`](../../run/SKILL.md). The harness itself is
covered in [`testing-harness.md`](testing-harness.md).

## Do this

**A hang is a retry loop.** Reboot retries instead of failing. It
retries a raising `initialize` forever with backoff, a lock wait after
30 s, a transaction presumed deadlocked, and a workflow's failed
attempt. So "nothing is happening" almost always means "something is
failing quietly, over and over". Find the failure:

1. **Rerun with `pytest -s`.** Pytest's output capture hides the
   runtime's log, and the log holds the real exception and its retry
   line:

   ```bash
   uv run pytest -s tests/chain_test.py -k "sells a seat"
   ```

   Look for `... failed with <Exception>; will retry after backoff ...`.

2. **If the log is silent too, dump every thread's stack** at the
   wedge:

   ```bash
   PYTHONFAULTHANDLER=1 timeout -s ABRT 300 uv run pytest -s tests/chain_test.py
   ```

   (or `kill -ABRT <pid>` on a hung run started with
   `PYTHONFAULTHANDLER=1`). An idle event loop means the code is
   awaiting something that never arrives. Look upstream of the await,
   not at it.

3. **Bisect with a scratch test** that boots progressively more of the
   app: servicers only, then `initialize`, then the failing call. Four
   such runs isolated a hang that four theory-driven code changes had
   not (theater-network, 1.4.0).

4. **Trust only the exit code of the command you meant.** Turn on
   `set -o pipefail` before any pipeline, and require a pytest summary
   line before you call a run green:

   ```bash
   set -o pipefail
   uv run pytest tests/ 2>&1 | tail -n 40   # exit is pytest's, not tail's
   ```

   Without `pipefail`, `cmd | tail` reports `tail`'s exit code. That
   produced two false "suite passed" reports (theater-network, 1.4.0).

5. **Give every unattended run its own timeout**, at about twice its
   measured runtime. Report "timed out" separately from "no summary".
   Check whether a quiet run is alive and working, or idle:

   ```bash
   ps -o pid=,%cpu=,etime= -p $(pgrep -f "pytest tests/")
   ```

## Never

- **Calling a run with no summary line a pass.** Pytest has died
  mid-run with no summary, no traceback and no non-zero exit. One such
  run was reported "0 failed" while an `F` was already in its dots
  (reboot-crm).
- **Running the suite while `rbt dev run` watches the same tree.** An
  edit makes the watcher regenerate `backend/api/**`
  (`Application modified; restarting`), and a suite that already
  imported those modules starts failing with `Method not found!` on
  methods that exist. Stop the dev app, or don't edit, while the suite
  runs.
- **Iterating on a state shape while the watcher is live.** A
  hot-restart can persist a field type that lived for seconds, and the
  corrected code is then refused as an incompatible change. Write the
  API edit once in its final form, or stop the watcher while you
  iterate (theater-network, 1.4.0). See
  [`api-schema-evolution.md`](api-schema-evolution.md).
- **Counting log lines to measure progress.** Effect-validation lines
  are logged once per method, then silenced for 5 minutes. A long seed
  looks hung, and counts mean nothing. Read progress from actor state
  with `rbt inspect`.
- **Trusting a browser tab across a backend restart.** It keeps
  retrying dead subscriptions and stops receiving pushes. Reload every
  open tab after every restart or expunge.

## Limits

- A failing `initialize` never fails the run. `rbt dev run` keeps
  retrying, and `Reboot().up()` never returns
  ([`lifecycle-initialize-hook.md`](lifecycle-initialize-hook.md)).
- A per-actor lock wait gives up after 30 s and is retried (1.6.0
  source). A contended transaction shows up as repeated waits, not as
  an error.
- Effect-validation warnings are rate-limited to one per method per
  5 minutes (1.6.0 source).
- Parallel harness runs (`-n auto`, `-n4`) and occasionally serial ones
  have hung at zero CPU with no output. No cause has been established
  (reboot-crm). The timeout in step 5 is the only guard.

## Scales as

- A long-lived `rbt dev run --watch` session measured about 14% slower
  after 12 reloads, and a restart fully recovered it. Restart the
  backend before measuring anything, and check `uptime` for ambient
  load first (theater-chain, 1.4.1).

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `initialize for application '...' failed with ...; will retry after backoff ...` | `initialize` raises on every attempt. This is the cause of a "hung" `up()` | Fix the named exception |
| `Application modified; restarting` | The dev watcher reloaded after a file change | Don't run the suite against a watched tree |
| `StatusCode.UNIMPLEMENTED details = "Method not found!"` | A missing servicer, a watcher restart mid-suite, or (observed, unexplained) a start-up race | Check `servicers=`, stop the watcher, rerun the file alone |
| `Not expecting stream to ever be done` (browser console) | The tab outlived its backend | Reload the tab |
| `Failed to flush monotonic clock high water mark: IO error: No such file or directory` | State was expunged under a running app | Stop, then restart, per [`../../run/SKILL.md`](../../run/SKILL.md) |
| `has switched type from` | The watcher persisted a transient field type | Restore the persisted type, or expunge dev state |

## See also

- [`../../run/SKILL.md`](../../run/SKILL.md): stop, restart, expunge
- [`testing-harness.md`](testing-harness.md): harness hangs and errors
- [`lifecycle-seeding.md`](lifecycle-seeding.md): slow seeds and effect validation
