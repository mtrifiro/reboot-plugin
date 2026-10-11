---
id: crm-kit-21
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §3"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/servicer-workflow-calls.md
  - python/references/servicer-workflow-wait.md
tags: [error-text]
cluster: "4.4"
duplicate_of: reboot-crm-49
still_applies: no
status: Resolved
resolved_by: "python/references/servicer-workflow-calls.md § Never"
---

# The callback of an inline write must be async def; the error names the return type

**What happened.** `ref().per_workflow("...").write(context, fn)` awaits `fn`. A plain `def` fails with `TypeError: object str can't be used in 'await' expression`, which names the return type, not the missing keyword. §11: the "Atomic Wait-and-Update" `try_claim` in `servicer-workflow.md` must be `async def`.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** `servicer-workflow.md` "Atomic Wait-and-Update" (§11).

**Checked at 1.6.0.** `python/references/servicer-workflow-calls.md` § Never (line ~127) lists `def try_claim(state) -> bool:` passed to `.write`; `servicer-workflow-wait.md` line ~76 now writes `async def try_claim`.
