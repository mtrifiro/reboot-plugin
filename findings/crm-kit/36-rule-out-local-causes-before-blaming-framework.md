---
id: crm-kit-36
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §6"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/lifecycle-dev-loop.md
  - python/references/testing-harness.md
tags: [testing, operations, error-text]
cluster: ""
still_applies: yes
status: Resolved
resolved_by: "build/templates/README.md § Files"
---

# Rule out local causes before blaming the framework: each looks exactly like a framework flake

**What happened.** The checklist: orphaned `main.py`/Envoy processes give hangs and `Address already in use`; the dev loop regenerating mid-run gives `Method not found!` on unrelated methods (any file edit, web-only included, or `rbt generate` triggers it; stop the dev loop and edit nothing during a run you must trust); a servicer missing from the harness gives `Method not found!` on the *same* method every time; `ALLOWED_EMAIL_DOMAINS` or `ALLOWED_EMAILS` set in the shell fails every scenario with `PermissionDenied` (run under `env -u ...`); two suites at once, or a suite beside `rbt dev run` in the same directory, deadlock the seed on a singleton lock (`PRESUMED_DEADLOCK`, retried forever).

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not named by the source.

**Checked at 1.6.0.** `python/references/lifecycle-dev-loop.md` § Never covers the suite beside a watching `rbt dev run` (`Method not found!`); `testing-harness.md` § Limits covers the missing servicer; `run/references/stop-restart-reset.md` covers orphans. `PRESUMED_DEADLOCK` from two concurrent suites on a singleton is not mentioned anywhere under `skills/` (grep).

**Resolution (2026-10-10).** `scripts/doctor.sh` in every template runs the rule-out-local-causes list in one command: this project's processes left by an earlier session, the state lock's holder, a test run in progress and two suites at once, the allowlist variables in the shell, and who serves each of the project's ports and from which directory; the run skill and `stop-restart-reset.md` point at it.
