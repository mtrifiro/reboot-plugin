---
id: reboot-air-150-01
project: reboot-air-150
source: "reboot-air/reboot-findings.md §1"
reboot_version: 1.5.0
severity: unrated
target: plugin
names:
  - dashboard/SKILL.md
tags: [version-drift, error-text, operations]
cluster: "A"
still_applies: no
status: Obsolete
resolved_by: ""
---

# dashboard skill passes a flag rbt dashboard rejects

**What happened.** `rbt: error: unrecognized arguments: --api-directory=api`. `rbt dashboard --help` on 1.5.0 lists only `--config`, `--default-config`, `--working-directory`, `--port`. Workaround: run `uv run rbt dashboard` with no flags; it finds `api/` via `.rbtrc`'s `generate api/` line.

**Expected.** The skill text should drop the flag.

**Repro.** Run the command in `skills/dashboard/SKILL.md` Step 4: `uv run rbt dashboard --api-directory=api`.

**Where in the skills.** `skills/dashboard/SKILL.md`, Step 4.

**Checked at 1.6.0.** No `--api-directory` appears anywhere under `skills/` now (grep), including `dashboard/SKILL.md`.
