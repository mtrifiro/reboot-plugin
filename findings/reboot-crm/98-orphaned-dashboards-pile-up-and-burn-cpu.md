---
id: reboot-crm-98
project: reboot-crm
source: "Observed directly on the developer's machine, 2026-10-08 (not from REBOOT_FINDINGS.md)"
reboot_version: 1.6.0
severity: yellow
target: framework
names:
  - dashboard/SKILL.md
  - run/SKILL.md
tags: [operations, cost]
cluster: "F"
still_applies: yes
status: Open
resolved_by: ""
---

# Dashboards outlive their sessions, pile up, and each worker can sit at ~67% CPU; SIGTERM to a backend orphans its worker and Envoy

**What happened.** Three `rbt dashboard` instances for reboot-crm were
still running, started by earlier agent sessions 2h10m, 2h55m and
8h54m before. Each was a `python -m reboot.dashboard.backend.main`
launcher reparented to launchd (ppid 1, since the `rbt dashboard`
front process had exited), plus a worker
(`.../reboot/dashboard/backend/main.py`). Together they used ~1.5 GB
RSS (workers ~320, ~320 and ~645 MB), and **every worker sat at a
steady 67–68% CPU**, about 2 of 10 cores. None served the project's
dashboard port (`.rbtrc`: `dashboard --port=9872`), so `rbt dev run`
couldn't find them, and each new session started another. Each was
listening only on its own random ports (e.g. `*:61783`, `*:61812`).
Separately, an Envoy from the plugin's shim (`.../reboot/bin/envoy-v1.38.4/envoy`)
was left at ppid 1, holding `127.0.0.1:59174`.

Reproduced in the same session:

- Killing the `rbt dashboard` front process (SIGKILL, as at session
  end) leaves the backend running with ppid 1. This holds whether its
  stdout is a file or a pipe that has been closed. `rbt dashboard`
  does not take its backend down with it.
- **SIGTERM to the backend stops it but leaves both its worker and its
  Envoy running with ppid 1**, the worker at ~225 MB and Envoy still
  holding its ports. So a "clean" stop still leaks processes. The
  skill's Step 3 uses `kill -INT`, which was not tested.
- Envoy is the backend's child and serves the dashboard port. Killing
  Envoy alone leaves the backend running and idle.

**Not reproduced: the CPU spin.** A fresh dashboard, and the same
dashboard orphaned in each of the ways above, idled at 0.0–0.5% CPU
for several minutes. What makes a worker spin is unknown. Two leads,
both untested: the "Pyright out of Node heap" known issue
(`WatchCode' failed with SystemAborted`) seen on this project's large
generated tree, retried in a loop; or the watch tasks retrying a gone
app address ("Watch tasks outlived their app"). The spinning
processes were killed before they could be profiled. Next time,
`sample <worker pid> 5` (macOS) or `py-spy dump --pid <worker pid>`
before killing.

**Expected.** Framework: `rbt dashboard` should take its backend down
when it exits (or the backend should exit when its parent goes away),
and the backend should stop its worker and Envoy on SIGTERM/SIGINT
(e.g. run them in its process group and signal the group). An idle
worker shouldn't use measurable CPU.

**Repro.**

```sh
cd reboot-crm
BROWSER=true uv run rbt dashboard &        # BROWSER=true keeps the tab closed
pkill -9 -f 'rbt dashboard'                # backend now has ppid 1
kill <backend pid>                         # worker + Envoy now have ppid 1
ps -axo pid,ppid,command | grep -E 'dashboard/backend/main|reboot/bin/envoy'
```

**Where in the skills.** `dashboard/SKILL.md` Step 3 stops an earlier
dashboard only from the same project root, only when the skill runs
again, and with `kill -INT <pid>` on the backend alone. The Known
issues table covers the dashboard outliving its listener and a killed
dashboard's Envoy holding 9871. It says nothing about the worker
leaking, orphans piling up across sessions, or the CPU cost. Plugin
mitigation: `hooks-handlers/orphans.sh` (SessionStart) now reports
orphaned backends older than an hour, plus stray workers and Envoys,
and tells the agent to offer to stop them.
