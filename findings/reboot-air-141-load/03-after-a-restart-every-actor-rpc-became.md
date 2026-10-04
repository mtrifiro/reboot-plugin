---
id: reboot-air-141-load-03
project: reboot-air-141-load
source: "reboot-air/REBOOT_LOAD_TEST_FINDINGS.md Finding 3"
reboot_version: 1.4.1
severity: unrated
target: framework
names: []
tags: [cost, operations]
cluster: "D"
still_applies: unknown
status: Open
resolved_by: ""
---

# After a restart every actor RPC became about 50x slower

**What happened.** The application was restarted to clear the wedged actor from Finding 2: same machine, code, and state directory, same `rbt dev run --no-chaos`. Afterwards every actor RPC was roughly 50x slower and did not recover over about 15 minutes. Measured sequentially from one client, before vs after restart: `Airline.routes` 2ms vs 95-102ms; `Flight.details` 1ms vs 49-51ms; `Airline.search_flights` (pair) 20ms vs 1.97-2.00s; `Airline.active_flights` 63ms vs 2.97-3.02s. Whole-workload throughput went from 172 rps to 1.3 rps at the same concurrency. Ruled out by the author: HTTP/proxy layer (plain `GET /__/oauth/start` stayed about 2ms); CPU (backend at 0-1.6%); one hot actor (different actors slowed by the same factor); data volume (172 rps was measured on the same state minutes earlier); a cold cache (three identical calls returned 2.97s / 3.02s / 2.97s); chaos mode (`--no-chaos` still on the supervisor command line); orphaned duplicates (one Envoy and one app process tree on the port). The one distinguishing detail: the restart was done by SIGTERM to the application process and letting the `rbt dev run` supervisor respawn it, but the supervisor did not respawn on its own; the process stayed down five minutes until a source file was touched and the watcher fired. Concurrency amplified it (`search_flights` 2.0s sequential, 10.4s median with six concurrent users), suggesting serialisation. Reported as an observation, not a diagnosis; may be a dev-mode artifact. Source severity: unknown.

**Expected.** Not recorded.

**Repro.** Not recorded beyond the description above: restart via SIGTERM of the application process under `rbt dev run --no-chaos`, wait for the watcher to restart it, then measure sequential calls.

**Where in the skills.** No skill is named. Related to the ops guidance in `run`.

**Checked at 1.6.0.** Not checked; target is `framework` (an upstream observation, not a skill claim).
