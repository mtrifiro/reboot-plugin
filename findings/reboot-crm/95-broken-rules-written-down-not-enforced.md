---
id: reboot-crm-95
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md A.14"
reboot_version: 1.6.0
severity: yellow
target: primer
names:
  - python/references/lifecycle-project-setup.md
tags: [operations, testing]
cluster: "4.6"
still_applies: unknown
status: Open
resolved_by: ""
---

# The rules that have been broken are written down, not enforced (Claude Code hooks)

**What happened.** Two rules in `docs/REBOOT_PRACTICES.md` exist because breaking them cost something, and both were broken again. (1) Back up production on its own: revision 16 shipped unbacked on 2026-09-30 because the backup was chained with `;` and grepped; on 2026-10-04 the backup before revision 19 was piped through `tail`, which hides its exit status (the output showed a complete export, so nothing was at risk). (2) Nothing that regenerates or rewrites code while the suite runs: `rbt generate`, `rbt dev run` and file edits mid-suite make tests abort `Unimplemented` on unrelated methods; on 2026-10-02 starting a Vite server mid-suite timed out two browser sign-ins. Status: done 2026-10-04: `.claude/settings.json` runs `scripts/hooks/guard.py` before every Bash, Edit and Write call; `scripts/suite.sh` holds `.suite-running` with its pid; tested on twenty-five sample calls. The hook's first version refused its author's own Markdown edit that named the script before a `|`, so it now matches the script only where run as a command.

**Expected.** Claude Code `PreToolUse` hooks: a lock file written by `suite.sh` and hooks refusing codegen/dev-server commands and edits under `backend/`, `api/`, `tests/`, `web/src/` while it names a live process; and a hook refusing any command that runs `backup.sh` with `|`, `;`, `&&` or `||` after it. Each refusal names the rule and finding. A deploy script would make the second hook mostly redundant.

**Repro.** Not recorded.

**Where in the skills.** Possible home: the plugin's hooks and project template (`hooks/hooks.json`, `lifecycle-project-setup.md`).

**Checked at 1.6.0.** `lifecycle-project-setup.md` was grepped for hook/CLAUDE.md guidance and none found; the plugin ships `hooks/hooks.json` and `auto-approve.sh` only.
