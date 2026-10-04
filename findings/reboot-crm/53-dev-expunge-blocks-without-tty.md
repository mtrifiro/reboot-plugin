---
id: reboot-crm-53
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P3.17"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - run/SKILL.md
  - python/references/lifecycle-rbtrc.md
  - python/references/api-schema-evolution.md
tags: [operations, error-text]
cluster: "F"
still_applies: yes
status: Open
resolved_by: ""
---

# rbt dev expunge blocks forever without a tty

**What happened.** `uv run rbt dev expunge` asks for confirmation. Run from a script with stdin closed it neither proceeds nor fails; it sat until killed. The flag is `--yes` (help: "skip the confirmation prompt"), but the skills that mention expunge do not. (Same friction as student-system-12 and student-sor-15.)

**Expected.** Fixes proposed: detect the absent tty and fail immediately with "no terminal to confirm on; pass `--yes`" (framework); every place the skills mention `rbt dev expunge` shows `--yes`, since scripted use is the normal use.

**Repro.** Run `uv run rbt dev expunge` with stdin closed.

**Where in the skills.** `python/references/lifecycle-rbtrc.md` (~line 49), `python/references/api-schema-evolution.md` (~line 177), `run/SKILL.md`.

**Checked at 1.6.0.** No skill mentions `--yes` for `rbt dev expunge` (grep `--yes` finds only `npx --yes wrangler` in `deploy/SKILL.md`); `lifecycle-rbtrc.md` and `api-schema-evolution.md` show `rbt dev expunge` without it.
