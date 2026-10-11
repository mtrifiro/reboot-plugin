---
id: new-crm-01
project: new-crm
source: "new-crm/docs/PATCHES.md §Patch A"
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

# Patch A, jit.off(): on macOS arm64 every live reader hangs ~60 s after a backend restart

**What happened.** Two edits to installed package files, taken from the crm-kit's `lessons.md` §1. Without Patch A (macOS arm64), after a backend restart every live reader hangs ~60 s with `Unavailable: ping timeout` while Envoy burns CPU, or writes silently do nothing. Re-apply after every `uv sync`, `reboot==` bump, fresh clone, uv cache prune or plugin upgrade: any reinstall reverts it silently. After patching, stop the dev loop, kill its orphans (`ps -eo pid,ppid,command | grep -E 'new-crm.*(main\.py|envoy)'`) and restart.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `run/references/stop-restart-reset.md` § Errors you will see and `errors.md` document the symptom; no `jit.off` patch under `skills/` (grep).
