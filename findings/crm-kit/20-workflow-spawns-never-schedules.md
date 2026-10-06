---
id: crm-kit-20
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §3"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/servicer-workflow-declare.md
  - python/references/scheduling-basic.md
  - python/references/scheduling-recurring.md
tags: [error-text, negative-space]
cluster: "4.1"
duplicate_of: reboot-crm-14
still_applies: no
status: Resolved
resolved_by: "python/references/servicer-workflow-declare.md § Never; python/references/scheduling-basic.md § Never; python/references/scheduling-recurring.md § Never"
---

# From a workflow, schedule with spawn(when=...), never schedule(when=...); mypy does not catch it

**What happened.** Which context each builder accepts (generated client, Reboot 1.6.0): `self.ref().schedule(when=...)` takes a `WriterContext` or `TransactionContext`; `ref(id).schedule(when=...)` on another actor takes a `TransactionContext` only; `ref(id).spawn(when=...)` takes a `WorkflowContext` or `ExternalContext`. From a workflow `schedule(...)` raises `TypeError: ... WorkflowContext is not an instance or subclass of ... TransactionContext` and retries forever. mypy misses it (the generated methods carry `# type: ignore[misc]`), so every context mismatch is a runtime discovery. Example: `await Chat.ref(id).per_workflow(f"Retry turn {n}").spawn(when=delay).turn(context, turn=n)`. §11: `servicer-workflow.md`, `scheduling-basic.md` and `scheduling-recurring.md` had no `spawn` anywhere.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** `servicer-workflow.md`, `scheduling-basic.md`, `scheduling-recurring.md` (§11).

**Checked at 1.6.0.** The three `§ Never` sections named carry the rule (canonical reboot-crm-14); `scheduling-recurring.md` and `errors.md` index the `WorkflowContext is not an instance or subclass` TypeError with fix `spawn(when=...)`.
