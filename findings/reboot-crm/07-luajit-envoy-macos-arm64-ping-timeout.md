---
id: reboot-crm-07
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P1.1"
reboot_version: 1.6.0
severity: red
target: plugin
names:
  - run/SKILL.md
tags: [operations, cost, error-text]
cluster: "F"
still_applies: yes
status: Open
resolved_by: ""
---

# LuaJIT in Envoy on macOS arm64 pins Envoy for ~10 minutes after every restart; every fan-out then dies with Unavailable: ping timeout

**What happened.** The Leads page "took 30 seconds to paint". Measured 2026-09-19 (Reboot 1.6.0, `rbt dev run --no-chaos`, macOS): after any backend restart (which `--watch` triggers on every backend file save) every reactive reader over the browser websocket hangs and aborts after 60-70 s with `rbt.v1alpha1.Unavailable: ping timeout`; the React client retries and nothing paints until the window ends. With a controlled restart, 8 consecutive loads failed at 68-70 s each, then at +610 s the page painted in 6.7 s and every later load in 0.4 s (window about 600 s in both runs). During the window the three `main.py` processes are idle (~1% CPU) while Envoy's internal trusted listener carries a storm (`downstream_rq_total` +27/s, `downstream_rq_rx_reset` +43/s, 100-280 active). With the runtime's event-loop diagnostics on, the dev log shows nothing. Envoy debug log: 89 of 93 requests are `/rbt.v1alpha1.React/Query` with `x-reboot-internal-call`, naming `Lead` actors, i.e. the `Leads.summaries` reader's `Lead.forall(ids).summary` fan-out (106 leads) re-executed about every 4 s and cancelled. A tab already open at restart painted after one burst; a fresh page load inside the window stalled; with no browser connected the window is silent. Root cause (two sessions, same Envoy): Envoy itself was the busy process (400-690% CPU, 7 of 10 workers pinned); `sample` shows time in macOS `libunwind` under C++ exception unwinding through JIT-generated frames; an `lldb` breakpoint on `_Unwind_RaiseException` caught class `LUAJIT` code 2 (`LUA_ERRRUN`) thrown by LuaJIT's error path and caught inside Lua. These are LuaJIT trace aborts, not script errors: the compiler repeatedly tries to compile the hot SHA-1 loops of Reboot's Lua routing filters (the server-id filter SHA-1s every state ref in pure Lua against a 16,384-entry shard table, in a script of about 1 MB), fails (on macOS arm64 executable memory needs `MAP_JIT`), and retries until its penalty counters blacklist the code about ten minutes later. While workers unwind they do not answer HTTP/2 keepalive pings, so internal gRPC channels die with `ping timeout`. Proof: prepending `if jit then jit.off() end` to every filter (`reboot/routing/envoy_config.py::_lua_any`) gave Envoy at 0.1-2.2% CPU, zero cancels, and an instant paint on a fresh reload inside the window. Each watch-restart also leaks an `envoy` process (ppid 1, xDS stream never connects); four were running. Seen again 2026-09-23: a `git worktree` needs its own venv, and `uv sync` installs a clean `reboot==1.6.0`, silently dropping both local patches (this one and the `maxBuffer` patch in reboot-crm-08); this one did not announce itself: the app served reads and returned 200, but writes (sign-in, Continue on the display-name screen) did nothing with no error, and only `%CPU` of 98.6% on the envoy process revealed it.

**Expected.** A restarted dev app answers readers within seconds; readers fail fast with a retryable error rather than hang until a 60 s keepalive death; old Envoys are reaped on restart. Fix list in the source: (1) `jit.off()` in the Lua filters (one line, everywhere, recommended as a point release); (2) stop SHA-1 in Lua per request (set the shard as a header); (3) reap orphaned Envoys on watch-restart; (4) `run/SKILL.md` names the symptom (every reader dying with `Unavailable: ping timeout` for ~10 minutes after a restart) and the venv patch; (5) print a warning when the Lua filters are generated without the workaround on macOS arm64.

**Repro.** With persisted state and a few live readers open in a browser: `touch backend/src/servicers/common.py`, reload, watch the console for `Unavailable: ping timeout`, and watch `curl http://<envoy admin>/stats | grep 'grpc_json.downstream_rq_rx_reset'` climb (admin address is in `--admin-address-path` on the envoy command line). Cost: ten minutes of an unusable app per edit; an afternoon spent optimising a page that was never slow.

**Where in the skills.** `run/SKILL.md` (no known-issues or symptom note).

**Checked at 1.6.0.** `run/SKILL.md` has no mention of `ping timeout`, LuaJIT or Envoy CPU (grep across run/dashboard/python found nothing).
