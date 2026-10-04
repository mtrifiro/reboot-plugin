---
id: reboot-crm-49
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P3.13"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - python/references/servicer-workflow.md
tags: [error-text, negative-space]
cluster: "4.4"
still_applies: yes
status: Resolved
resolved_by: "python/references/servicer-workflow-calls.md § Never"
---

# An inline writer's callback must be a coroutine, and the error does not say so

**What happened.** `Leads.ref().per_workflow("...").write(context, fn)` awaits `fn`, so a plain `def fn(state) -> str` fails with `TypeError: object str can't be used in 'await' expression`, which names the returned type rather than the missing `async`. `servicer-workflow.md`'s "Atomic Wait-and-Update" example writes `def try_claim(state) -> bool` without `async`, reading as permission to do exactly this.

**Expected.** Fix the example (add `async`) and the message ("the callback passed to `write()` must be `async def`"). Recommendation: the example first.

**Repro.** Pass a plain `def` callback to `ref().per_workflow(alias).write(context, fn)`.

**Where in the skills.** `python/references/servicer-workflow.md` ("Atomic Wait-and-Update", ~line 1170).

**Checked at 1.6.0.** `servicer-workflow.md` line 1170 still reads `def try_claim(state) -> bool:` without `async`.
