---
id: reboot-crm-51
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P3.15"
reboot_version: 1.6.0
severity: yellow
target: framework
names:
  - dashboard/SKILL.md
tags: [operations]
cluster: "F"
still_applies: yes
status: Open
resolved_by: ""
---

# rbt dashboard can outlive its own port

**What happened.** A dashboard started two days earlier was still running (its `reboot.dashboard.backend.main` children alive on ephemeral ports) while nothing listened on 9871 any more. The browser tab kept a cached page with "live" off and no explanation, and a fresh `rbt dev run` connected to nothing because it finds a dashboard by that port. Restarting the dashboard fixed it.

**Expected.** The dashboard should exit (preferred) or rebind its listener when the front port dies, so the state is serving or not running.

**Repro.** Not recorded.

**Where in the skills.** `dashboard/SKILL.md` (Step 3 checks port 9871 with curl before deciding).

**Checked at 1.6.0.** `dashboard/SKILL.md` Step 3 (~line 87-93) only curls 9871; it has no note on stale dashboard processes.
