---
id: reboot-crm-93
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md A.12"
reboot_version: 1.6.0
severity: yellow
target: framework
names:
  - python/references/servicer-writer.md
  - python/references/scheduling-basic.md
tags: [pattern, negative-space]
cluster: "4.1"
still_applies: yes
status: Open
resolved_by: ""
---

# A writer can schedule only on itself, so every type grows the same hand_in workflow

**What happened.** A writer may `schedule()` only on its own actor (`servicer-writer.md`). To put work on another actor's queue, `Intelligence`, `Lead` and `Contact` each grew an identical workflow whose only job is to call `Leads.queue_by_hand`. Same limit as reboot-air-150-10.

**Expected.** One generic helper in the app. For Reboot: let a writer schedule a call on another actor, run after the writer commits, with the same guarantee the self-scheduled workflow gives.

**Repro.** Not recorded.

**Where in the skills.** `python/references/servicer-writer.md` (~lines 84-98) and `python/references/scheduling-basic.md`.

**Checked at 1.6.0.** `servicer-writer.md` (lines ~84-98) still says a writer schedules work on itself; `scheduling-basic.md` (~line 80) still implies any ref can be scheduled with no context caveat.
