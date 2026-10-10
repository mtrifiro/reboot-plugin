---
id: hotel-trial-01
project: hotel-trial
source: "hotel-app A/B build trial, 2026-10-05 (orig.jsonl, new.jsonl)"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - bin/uv
  - bin/node
  - bin/envoy
tags: [operations, error-text]
cluster: "F"
still_applies: yes
status: Resolved
resolved_by: "build/templates/README.md § Copy"
---

# The `bin/` tool shims fail with a bare "No such file" when `lib/` isn't beside them

**What happened.** Both builds in a hotel-app A/B trial ran with a
plugin directory whose `bin/` (a symlink) had no `lib/` next to it. Every
plugin shim the agent called failed at its first line of real work:
`install_uv.sh: No such file or directory`, then the same for
`install_node.sh` and `install_envoy.sh`. Both agents read the shim
source, diagnosed it, and fell back to the user's own `uv`, `node` and a
cached Envoy, at the cost of several turns each. The original-skills
run reported it as "Broken tool shims … (a missing `lib/` directory)".
The shims find the installer as `$PLUGIN_ROOT/lib/install_<tool>.sh`,
where `PLUGIN_ROOT` is `CLAUDE_PLUGIN_ROOT`, else the shim's directory's
parent; neither checks that the installer exists.

**Expected.** A shim that can't find its installer says which file is
missing, where it looked, and what to do (reinstall the plugin, or set
`CLAUDE_PLUGIN_ROOT`). Resolving the shim's own path through symlinks
(`realpath "$0"`) would also make a symlinked `bin/` work.

**Repro.** Make a directory with a `.claude-plugin/plugin.json` and a
`bin` symlink to the plugin's `bin/`, but no `lib/`; load it with
`claude --plugin-dir <dir>`; run `uv --version` in a session.

**Where in the skills.** `bin/uv`, `bin/uvx`, `bin/node`, `bin/npm`,
`bin/envoy`, `bin/cloudflared` (each delegates to `lib/install_*.sh`).

**Checked at 1.6.0.** The trigger was the trial's wrapper layout, not a
normal marketplace install, which copies `lib/`. The unclear failure
applies to any partial or symlinked install.

**Resolution (2026-10-10).** Every shim in `bin/` resolves its own path through symlinks and, when `lib/` is not beside it, says which directory it looked in, that the plugin's `lib/` must sit beside its `bin/`, and to reinstall or set `CLAUDE_PLUGIN_ROOT`, instead of a bare "No such file".
