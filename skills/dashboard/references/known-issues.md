---
title: Dashboard Symptoms and Their Fixes
impact: MEDIUM
impactDescription: "A dashboard that outlived its session, its port or its project shows a wrong Call Graph, stale Models or another app's API, and looks like a framework fault"
tags: dashboard, call graph, pyright, port, orphan, stale, models
summary: "Each dashboard symptom (wrong Call Graph, stale Models, held port, old workers) with its meaning and fix."
step: run
applies: [mcp-ui, web-app, backend-only]
always: false
when: "the dashboard shows a wrong Call Graph, stale Models, another project's API, or won't start on its port"
verified: 1.6.0
docs: ""
---

# Dashboard Symptoms and Their Fixes

## When you are here

The dashboard is up but wrong: the Call Graph says `0 calls`, the
Models page shows types the project no longer has, the port is held,
or `rbt dashboard` workers from earlier sessions are still running.
Each row below is a symptom seen on a real project, with its meaning
and the fix that worked.

## Do this

| Error / symptom | Meaning | Fix |
| --- | --- | --- |
| `RuntimeError: Cannot add watch ... it is already scheduled` from watchdog at start, then the dashboard URL | The dashboard schedules its file watch twice on macOS (restaurant-3, 1.6.0) | Harmless when the URL follows; nothing to do |
| Call Graph shows `0 calls` and "Your application imports generated code that does not exist yet ... Run `rbt generate`" although the generated code exists; one orphaned `node .../langserver.index.js` per analysis | Orphaned pyright child, hung shutdown (1.5.0); the 1.6.0 source kills pyright's process group on shutdown, so it should not recur | `pkill -f langserver.index.js`; the graph then publishes. The plugin's session-start report names such an orphan |
| Call Graph never publishes; the dashboard's Node sits at its heap limit, retrying | pyright out of Node's default heap on a mid-sized app (reboot-crm, 1.6.0) | The shims set `NODE_OPTIONS=--max-old-space-size=12288` for `rbt dashboard`; set a larger one yourself if it recurs |
| Same banner, status `CODE NOT CHECKED YET`, and the dashboard log shows `RuntimeError: pyright exited` / `WatchCode' failed with SystemAborted` | Pyright out of Node heap on a large generated tree; the banner wrongly blames generated code (reboot-crm, 1.6.0) | Start with `NODE_OPTIONS="--max-old-space-size=12288" uv run rbt dashboard` |
| "code checked at" an old time, deleted methods still drawn, or "Your API files changed since the generated code was written" right after `rbt generate` | Stale analysis after a dashboard restart (reboot-crm, 1.6.0) | Run `uv run rbt generate` once more |
| Dashboard log keeps retrying an old app address (`WatchApi` ... `Connection refused`) after an expunge and restart | Watch tasks outlived their app (reboot-crm, 1.6.0) | Stop the dashboard, delete `.rbt/dashboard`, restart it |
| Probe on 9871 succeeds but the page shows another project's API | Another project's dashboard got 9871 first | Step 3: start with `--port=<port>` |
| Models page shows types the project no longer has, no call lines, footer "API checked at" frozen at an earlier time | A dashboard from an earlier project in the same folder; the cwd check passes (1.6.0) | Step 3: stop it, start fresh, `uv run rbt generate` once |
| Tab shows "live" off; a fresh `rbt dev run` finds no dashboard; `rbt dashboard` processes still running | The dashboard outlived its 9871 listener (reboot-crm, 1.6.0) | Stop it and start a fresh one |
| Next start fails with `cannot bind ... Address already in use` on 9871 | A killed dashboard left its Envoy holding the port (student-system, 1.5.0) | `lsof -t -iTCP:9871 -sTCP:LISTEN \| xargs kill`, after checking the holder (see the [run skill](../../run/SKILL.md) § "Stop, restart, reset") |
| `rbt: error: unrecognized arguments` | A flag `rbt dashboard` does not take (e.g. `--no-open-browser`, `--api-directory`) | Use only the four flags in Step 4 |
| Dashboard workers from earlier sessions, each at about 67% CPU, together over 1 GB | `rbt dashboard` outlives its session; SIGTERM to its backend leaves the worker and Envoy (reboot-crm, 1.6.0) | The session-start report names them; kill the group; `scripts/doctor.sh` lists this project's |

## Never

- Restarting the app or regenerating to fix a dashboard symptom: the
  dashboard is a separate process; fix it on its own.
- Killing every `rbt` process on the machine: other projects' apps and
  dashboards share it. Kill by pid, found through the port.

## Limits

- Pyright's heap is Node's default; a mid-sized app can exhaust it and
  the dashboard cannot raise it itself.

## Scales as

- One dashboard per project, on its own port; each holds a pyright
  worker whose memory grows with the API.

## Errors you will see

The table above, by symptom.

## See also

- [`../SKILL.md`](../SKILL.md): starting the dashboard, and the port it
  should hold.
