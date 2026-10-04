---
id: reboot-crm-77
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P4.8"
reboot_version: 1.6.0
severity: green
target: plugin
names:
  - dashboard/SKILL.md
tags: [operations, error-text]
cluster: "F"
still_applies: unknown
status: Open
resolved_by: ""
---

# rbt dashboard cannot be told not to open a browser

**What happened.** `rbt dashboard` has only `--config`, `--default-config`, `--working-directory` and `--port`. `rbt dev run` has `--open-dashboard/--no-open-dashboard`, so the pairing is easy to assume; `--no-open-browser` fails with argparse's "unrecognized arguments" and exit 2, which in a background shell reads as the dashboard failing to start.

**Expected.** Add `--no-open-browser` to `rbt dashboard`, pairing with `rbt dev run`'s flag (recommendation: do it).

**Repro.** Not recorded.

**Where in the skills.** `dashboard/SKILL.md`.

**Checked at 1.6.0.** `dashboard/SKILL.md` (Step 5) opens the URL once itself; it does not pass any browser flag, but nothing warns that `--no-open-browser` does not exist.
