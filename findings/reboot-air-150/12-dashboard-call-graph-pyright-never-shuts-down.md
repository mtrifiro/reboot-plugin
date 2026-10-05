---
id: reboot-air-150-12
project: reboot-air-150
source: "reboot-air/reboot-findings.md §12"
reboot_version: 1.5.0
severity: unrated
target: framework
names:
  - dashboard/SKILL.md
tags: [operations, error-text]
cluster: "F"
still_applies: yes
status: Resolved
resolved_by: "dashboard/SKILL.md § Known issues"
---

# Dashboard Call Graph says "generated code does not exist yet" forever; its pyright subprocess never shuts down

**What happened.** `rbt dashboard`'s Call Graph shows 0 calls and "Your application imports generated code that does not exist yet, so the static call graph analysis cannot be done. Run rbt generate." while `backend/api/air/v1/air_rbt.py` exists and is current. Restarting the dashboard, wiping `.rbt/dashboard` and touching sources do not help; nothing is logged. Mechanism (`reboot/dashboard/backend/code_watcher.py` + `pyright.py`, reboot 1.5.0, macOS, Python 3.12): each iteration runs `_walk_and_analyze` (start pyright, analyze, `pyright.stop()`, then list the generated directory and write both to `Dashboard` state); the UI reports MISSING whenever an API module has no entry in `Dashboard.generated`. `Pyright.start` spawns `sys.executable -m pyright.langserver --stdio`, the pyright-python wrapper, which `subprocess.run`s `node .../langserver.index.js` as a grandchild sharing the stdio pipes. `Pyright.stop` does `terminate()` then `await wait()`; SIGTERM kills only the wrapper, node is orphaned (ppid 1) holding the stdout pipe, so `wait()` never completes, the iteration never reaches `UpdateCode`, and one node process leaks per iteration. Standalone, walk took 0.5 s, analysis 3.1 s, then it hangs in `stop()`; killing the orphan completes the script and made the live graph show "10 calls between 4 state types". Workaround: `pkill -f langserver.index.js` after the dashboard has been up a few seconds.

**Expected.** Fixes to consider (framework side): launch node directly, or start the wrapper with `start_new_session=True` and kill the process group, or send LSP `shutdown`/`exit` first, or close `stdin` and wait with a timeout. The UI should distinguish "generated module missing" from "analysis has not completed" and log when an iteration exceeds ~60 s.

**Repro.** Not recorded beyond the symptom and mechanism above.

**Where in the skills.** `dashboard/SKILL.md` (no known-issues section).

**Checked at 1.6.0.** `dashboard/SKILL.md` has no mention of pyright, `langserver` or the Call Graph.
