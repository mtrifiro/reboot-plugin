---
id: reboot-crm-28
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P1.18"
reboot_version: 1.6.0
severity: red
target: framework
names: []
tags: [negative-space, testing, operations, error-text]
cluster: "F"
still_applies: unknown
status: Open
resolved_by: ""
---

# Test servers listen on 0.0.0.0 (dual-stack IPv6) and macOS hands out ports held on IPv4, so servers collide with orphaned Envoys

**What happened.** Reboot's in-process servers listen on `f'{host}:0'` with `host = '0.0.0.0'` (`reboot/controller/server_managers.py:797`, `reboot/settings.py:217`); gRPC binds a wildcard as one dual-stack IPv6 socket, and the macOS IPv6 ephemeral allocator does not avoid ports held on IPv4 (TCP ports handed out in sequence, `net.inet.tcp.randomize_ports: 0`). A caller dialling `127.0.0.1:port` then reaches the orphan's IPv4 socket: Envoy answers HTTP 404 (gRPC `Unimplemented`) or nothing (hang). Experiment (505 scenarios x3 runs): clean 1,515 scenarios, 3 failed; with 6 orphaned Envoys 1,444 scenarios, 5 failed and 2 files timed out, and every server given an orphan's port failed (4 of 4). Direct measurement: an IPv6 dual-stack `[::]:0` bind was handed 200 of 200 held IPv4 ports, an IPv4 `127.0.0.1:0` bind 0; `SO_REUSEPORT` plays no part. Workaround: `tests/conftest.py` sets `server_managers.EVERY_LOCAL_NETWORK_ADDRESS = "127.0.0.1"` (12 orphans: 0 collisions, 0 hangs, 0 timeouts). The test database has the mirror problem: native in-process server listens dual-stack and reports `0.0.0.0:<port>`; a bare `TimeoutError` after ~45 s comes from `DatabaseClient` waiting on `channel_ready()` (`reboot/server/database.py:737`) when an IPv4 listener holds that port (reproduced 11 of 14 start-ups with a planted listener; 1 in 3,000 start-ups in the wild). Workaround: `DatabaseServer.address` returns `[::1]:<port>`. One failure, `UNAVAILABLE: Route not configured yet`, remains unexplained. The frames of that `TimeoutError` are lost because `reboot.bdd` runs the step via `asyncio.run_coroutine_threadsafe`.

**Expected.** Bind servers and the test database to the loopback address callers dial (`127.0.0.1`), or bind both families, or dial the family bound; have `DatabaseClient`'s 45 s wait name the address it gave up on; do not leave Envoys behind (see reboot-crm-15). Killing orphaned Envoys (parent pid 1) before a run is still worth doing.

**Repro.** `scripts/orphan_envoy_experiment.sh 3 6`, then `scripts/diag_report.py`; the allocator alone with a few lines of Python `socket`; database: `CRM_LANDMINE=1 CRM_BIND_LOOPBACK=0 uv run pytest tests/canary_full_test.py -k comes_up_and_goes_down --count 4`.

**Where in the skills.** Not a skill gap as written; relevant to `python/references/testing-harness.md` only if a note on orphaned Envoys and loopback binding is added.
