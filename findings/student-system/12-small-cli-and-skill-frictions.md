---
id: student-system-12
project: student-system
source: "student-system/reboot-findings.md §12"
reboot_version: 1.5.0
severity: unrated
target: plugin
names:
  - run/SKILL.md
  - dashboard/SKILL.md
  - python/references/api-methods.md
tags: [operations, version-drift, index-gap]
cluster: "F"
still_applies: yes
status: Open
resolved_by: ""
---

# Small CLI and skill frictions (expunge --yes, --api-directory, test warnings, docstrings as dashboard descriptions)

**What happened.** Four frictions. (1) `rbt dev expunge` asks a y/n question so it cannot run from a non-interactive prompt; `--yes` exists but the `run` skill does not mention it. (2) The `dashboard` skill passes `--api-directory=api`, which `rbt dashboard` 1.5.0 rejects (reboot-air-01); started plain it finds `api/` from `.rbtrc`. (3) Every test run prints deprecation warnings from inside Reboot (`from websockets.server import WebSocketServerProtocol`), one per test, filtered with `-p no:warnings`, which also hides the app's own warnings. (4) The dashboard reads a model's class docstring as its description; nothing in the `web-app` or `python` skills says so.

**Expected.** `api-methods.md` should say "docstrings on `Model` classes and `description=` on `Type` and methods are what the dashboard shows."

**Repro.** Not recorded.

**Where in the skills.** `run/SKILL.md`, `dashboard/SKILL.md`, `python/references/api-methods.md`.

**Checked at 1.6.0.** `--api-directory` is no longer in any skill (fixed). `--yes` for `expunge` is still unmentioned in `run/SKILL.md`, and `api-methods.md` has no note on docstrings feeding the dashboard.
