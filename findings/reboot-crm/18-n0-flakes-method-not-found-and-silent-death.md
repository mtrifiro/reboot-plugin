---
id: reboot-crm-18
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P1.10b"
reboot_version: 1.6.0
severity: red
target: framework
names: []
tags: [testing, error-text, negative-space]
cluster: "4.4"
still_applies: unknown
status: Resolved
resolved_by: "python/references/testing-harness.md § Errors you will see"
---

# -n0 flakes anywhere in a file, and a dead run is indistinguishable from a clean one

**What happened.** Seven sequential `pytest -n0 tests/crm_test.py` runs on 2026-09-22/23: runs 1-5 with an `rbt dev run` and `rbt dashboard` alive (2 failed/323 passed; 2/316; 2/316; 318 passed; 318 passed), runs 6-7 with nothing else running (1 failed/317; 318 passed): roughly 0.4% of scenarios under load and 0.16% on a quiet machine, from samples too small to compare. The point is that run 6 failed at all. Run 8 (2026-09-23, idle) failed three scenarios, none at `Given the application is up`, each dying constructing a singleton: `crm.v1.crm_rbt.Leads.CreateAborted: aborted with 'Unimplemented': Received http2 header with status: 404`. Runs 9-15 (2026-09-24, dev loop stopped): five different scenarios across two files failed mid-file with `Unimplemented` / `Method not found!` (e.g. on `crm.v1.Pipeline.AddAccount`, `crm.v1.Team.Members`), each passing alone in under ten seconds; and three runs produced no result at all: pytest died with no summary line, no traceback and no non-zero exit (21 scenarios completed with 21 bytes of dots; 85 with 588 bytes; 363 of 375 with 404 bytes). A run reported as "0 failed" had in fact died with a genuine failure already on screen as an `F` in the dots. The same `Unimplemented` signature has a mundane cause: `rbt dev run` watching the tree regenerates `backend/api/**` on any file change and a suite that already imported those modules then serves a different set (dev log says `Application modified; restarting`); the flake is the same message with the dev loop stopped. Otherwise every failure is in `Given the application is up` (`reboot/bdd/steps.py:831`), with two signatures only: `grpc.aio._call.AioRpcError: status = StatusCode.UNIMPLEMENTED details = "Method not found!"` and `TimeoutError`. Mechanism that fits (from reading the code): `reboot/aio/servers.py:617` launches `wait_for_placement_client_then_ready()` with `asyncio.create_task` and never awaits it; `_ready` is awaited only in `internals/tasks_dispatcher.py:161`, so it gates task dispatch only; the gRPC server accepts requests before the placement client converges, so a request in that window is `Method not found!` and the state manager's ownership waits (`state_managers.py:677`, `:2122`) expire as `TimeoutError`. Measured 2026-09-28 with new diagnostics: every one of 1,716 `ServiceServer`s served requests for 0.18 to 0.59 s before `_ready` was set, but the harness waits it out (`Given the application is up` returns within 2 ms of the last server ready; 18 of 18 scenarios timed; 180 canary scenarios never failed), so the window does not by itself explain a mid-file `Method not found!`; the next one is to be caught with its server and port events. The author also notes two earlier drafts overclaimed from small samples.

**Expected.** A sequential run to be deterministic. Most helpful, in order: a non-zero exit when the process dies mid-run, and an error that distinguishes "this method does not exist" from "this application is not routable yet". Fix: await readiness before `up()` returns, or have the server refuse rather than misroute until the placement client has converged; at minimum fix the wording.

**Repro.** `uv run pytest -n0 tests/crm_test.py` several times, with `pgrep -f 'main.py|envoy'` empty first.

**Where in the skills.** Not applicable to a skill.

**Resolution (2026-10-10).** Rows in `testing-harness.md` § Errors you will see: a run that ends with no summary line and exit 0 died; the dual-stack port collisions on macOS and the `conftest.py` loopback setting; the `sys.excepthook` noise. `pytest-timeout` in the templates fails a hang on its own.
