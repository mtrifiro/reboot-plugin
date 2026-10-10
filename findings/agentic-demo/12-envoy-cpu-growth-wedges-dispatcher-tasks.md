---
id: agentic-demo-12
project: agentic-demo
source: "v 1.4.1 Reboot/Archive/agentic-demo/docs/reboot-learnings.md §11"
reboot_version: 1.4.0
severity: unrated
target: framework
names:
  - run/SKILL.md
  - python/references/patterns-load-and-benchmarking.md
tags: [cost, operations, error-text]
cluster: ""
still_applies: yes
status: Resolved
resolved_by: "run/references/stop-restart-reset.md § Errors you will see"
---

# Under sustained workflow traffic Envoy's CPU grows until internal pings time out, wedging dispatcher tasks in a retry loop that survives restarts

**What happened.** Repro: run a continuous workflow (`DemoRun.Caseload`, a `context.loop` creating actors every ~5 s) under `rbt dev run`, then start the full pytest suite (several in-process Reboot runtimes) on the same machine. Under the CPU starvation the dispatcher logs `Task '…' failed with CreateAborted/ResetAborted: aborted with 'Unavailable': ping timeout; will retry after backoff`. The wedge persists after the load is gone and across several graceful SIGINT restarts: the same task UUIDs retry `'Unavailable'` forever on the fresh process while the HTTP front door answers in ~10 ms. Only `rbt dev expunge` clears it. Escalation: it also happens with no external load. After an expunge and clean restart, the operation (one `context.loop` workflow, ~6 cross-actor RPCs per 5 s tick, two reactive browser subscriptions) wedged after about ten minutes with the same signature on `Create` calls, counters frozen. Root-cause isolation (measured): with no browser attached, 14 minutes ran with zero ping-timeout warnings (48 orders placed, 46 delivered, 36 cases resolved) while Envoy's CPU climbed monotonically: 70% of a core at t+4 min, 96% at t+8, 154% at t+14, from roughly one RPC per second. The author's chain: Envoy accrues CPU under sustained traffic (growth, not rate; it never comes down), browser subscriptions and polls push it to saturation, internal pings time out, dispatcher tasks fail `'Unavailable'` and retry forever, and a restart does not help because reconnecting clients re-saturate the fresh Envoy. This makes sustained continuous workflows on the 1.4.0 dev runtime unreliable past ~10 minutes. Mitigations that worked: dedupe redundant reactive subscriptions (per-tab streams halved), slow HTTP polls to 6–8 s, slower heartbeat (8 s), fewer `always`-scope reads per tick, `scripts/reset_live.sh` between long sessions, and never run the heavy test suite while the live operation is up.

**Expected.** Upstream checks the source asks for: whatever target or lease the dispatcher's retry path caches for a resumed task appears durable and is never re-resolved against the new incarnation; Envoy's monotonic CPU growth under a trickle of proxied RPCs looks like stream/connection accrual and deserves a profile.

**Repro.** A single long-running `context.loop` workflow that creates actors (~6 cross-actor RPCs per 5 s tick) plus two reactive browser subscriptions under `rbt dev run` on 1.4.0; wedges after about ten minutes. Faster: run the full pytest suite alongside it. The author calls this the highest-value repro in the repo.

**Where in the skills.** Framework (file upstream). Operationally relevant to `run/SKILL.md`. Compare reboot-crm-07 (LuaJIT post-restart Envoy window on macOS arm64, which ends after ~10 minutes, whereas this grows and survives restart) and theater-network-23 (per-request Envoy cost); related to item 10 here.

**Checked at 1.6.0.** `errors.md` and `run/references/stop-restart-reset.md` § Errors you will see list `Unavailable: ping timeout` only as the ~10-minute post-restart LuaJIT window, and `patterns-load-and-benchmarking.md` as a fan-out exceeding the request window. Nothing covers Envoy CPU growth under sustained traffic, `CreateAborted`/`ResetAborted` retry loops that survive a restart, or expunge as the only remedy. Not checked against the 1.6.0 runtime.

**Resolution (2026-10-10).** Rows in `stop-restart-reset.md` § Errors you will see: `ResetAborted: 'Unavailable'` against a dead incarnation's port after `kill -9`; the dispatcher wedge (`ping timeout; will retry after backoff`) that survives restarts; the stale-address `Participant/Prepare` loop after a mid-commit kill. Each names the expunge as the reset.
