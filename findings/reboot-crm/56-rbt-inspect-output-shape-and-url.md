---
id: reboot-crm-56
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P3.20"
reboot_version: 1.6.0
severity: yellow
target: framework
names:
  - inspect/SKILL.md
tags: [operations]
cluster: "F"
still_applies: unknown
status: Open
resolved_by: ""
---

# rbt inspect output shape and required --application-url

**What happened.** `rbt inspect state get` prints repeated fields inconsistently for scripting: some lists come back as `{"items": [...]}` and some as plain JSON arrays (both seen on `Account.signals`, `brief`, `stage_history`); scripts had to handle both. `--application-url` is required even against a local `rbt dev run`.

**Expected.** Emit repeated fields consistently as plain arrays; default `--application-url` to `http://127.0.0.1:<port from .rbtrc>` when present, removing the friction the `inspect` skill implies is absent.

**Repro.** Not recorded.

**Where in the skills.** `inspect/SKILL.md` (Connecting section).

**Checked at 1.6.0.** `inspect/SKILL.md` lines ~34-56 show `--application-url=<url>` in every example (so required is visible); output-shape inconsistency is not mentioned.
