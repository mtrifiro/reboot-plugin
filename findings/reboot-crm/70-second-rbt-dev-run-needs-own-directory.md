---
id: reboot-crm-70
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P4.1"
reboot_version: 1.6.0
severity: green
target: plugin
names:
  - run/SKILL.md
  - python/references/lifecycle-rbtrc.md
tags: [operations, negative-space, error-text]
cluster: "F"
still_applies: yes
status: Resolved
resolved_by: "python/references/lifecycle-rbtrc.md § Limits; run/references/stop-restart-reset.md § Never"
---

# A second rbt dev run of the same app needs its own directory

**What happened.** A throwaway seeded instance beside the real one took three tries. (1) `rbt dev run --port=9990 --application-name=scratch` is refused: "the flag '--application-name' was set multiple times; it can only be set once, including in the `.rbtrc` file"; no flag set by `.rbtrc` can be overridden from the command line, so the only way is a different directory with its own `.rbtrc` (absolute paths work). (2) From that directory, the venv's `rbt` binary directly fails with "Failed to find 'protoc-gen-reboot_python'. Please report this bug to the maintainers."; the plugin is in the venv's `bin/`, which only `uv run` puts on `PATH`; `uv run --project <repo> rbt dev run` works. (3) Neither the `run` skill nor `lifecycle-rbtrc.md` mentions either constraint.

**Expected.** Fix proposed: let command-line flags override `.rbtrc`; fix the `protoc-gen-reboot_python` message to say "run via `uv run`"; and a note in `run/SKILL.md` or `lifecycle-rbtrc.md` that a second instance needs its own directory and `.rbtrc`. Recommendation: the error message first.

**Repro.** Not recorded.

**Where in the skills.** `run/SKILL.md`, `python/references/lifecycle-rbtrc.md`.

**Checked at 1.6.0.** Neither `run/SKILL.md` nor `python/references/lifecycle-rbtrc.md` mentions a second instance or the `PATH`/`uv run` requirement (grep).
