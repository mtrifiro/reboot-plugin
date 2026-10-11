---
id: crm-kit-02
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §1"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - run/references/stop-restart-reset.md
tags: [operations, error-text]
cluster: "F"
duplicate_of: reboot-crm-07
still_applies: no
status: Resolved
resolved_by: "run/references/stop-restart-reset.md § Errors you will see"
---

# Patch A: LuaJIT in Envoy on macOS arm64 hangs every reactive reader after each restart; `jit.off()` removes it

**What happened.** After every backend restart (and `--watch` restarts on every save), every reactive reader hangs 60-70 s and dies with `rbt.v1alpha1.Unavailable: ping timeout`, for about 10 minutes; Envoy sits at 400-690% CPU while Python idles near 1%. Quieter version on a fresh checkout: pages render and `curl` returns 200, but writes silently do nothing. Cause: LuaJIT keeps failing to compile Reboot's Lua routing filters (macOS arm64 needs `MAP_JIT`) until it blacklists them. Fix: an idempotent script prepends `if jit then jit.off() end` to the source in `reboot/routing/envoy_config.py` `_lua_any`; verify the printed line ends `True`, stop the dev loop, kill orphans and restart (a running Envoy keeps its old filters); afterwards `ps -o %cpu=,command= -p $(pgrep -d, envoy)` should read a few percent. The patch edits an installed file, so every `uv sync`, `reboot==` bump, fresh clone or worktree, uv cache prune or plugin upgrade reverts it silently and it must be re-applied. Needed on macOS arm64, harmless elsewhere.

**Expected.** Not recorded beyond the local patch.

**Repro.** Not recorded.

**Where in the skills.** Not named by the source.

**Checked at 1.6.0.** `run/references/stop-restart-reset.md` § Errors you will see (line ~138) and `python/references/errors.md` (line ~97) document the symptom and cause and advise waiting it out; no `jit.off` patch appears anywhere under `skills/` (grep).
