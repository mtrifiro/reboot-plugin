---
id: crm-kit-18
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §3"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/servicer-workflow-wait.md
tags: [contradiction, negative-space]
cluster: "4.1"
duplicate_of: reboot-crm-05
still_applies: no
status: Resolved
resolved_by: "python/references/servicer-workflow-wait.md § Do this; python/references/servicer-workflow-wait.md § Never"
---

# An until callable returns a bool, always; any non-bool resolves the wait

**What happened.** Only a `bool` is tested for truth. `""`, `0`, `None` and `[]` all resolve the wait at once. The source's shape: `async def ready() -> bool: return (await Leads.ref().read(context)).queue_id != ""`. §11: `servicer-workflow.md` says `until` waits on any "truthy value", and `get_settled`'s "# None is falsy" is the bug.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** `servicer-workflow.md` (§11).

**Checked at 1.6.0.** `python/references/servicer-workflow-wait.md` § Do this and § Never carry the bool rule, per the canonical item reboot-crm-05.
