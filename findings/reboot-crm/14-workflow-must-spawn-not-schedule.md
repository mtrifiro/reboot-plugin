---
id: reboot-crm-14
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P1.8"
reboot_version: 1.6.0
severity: red
target: plugin
names:
  - python/references/servicer-workflow.md
  - python/references/scheduling-basic.md
  - python/references/scheduling-recurring.md
tags: [negative-space, contradiction, error-text]
cluster: "4.1"
still_applies: yes
status: Open
resolved_by: ""
---

# From a workflow you must spawn(when=...), not schedule(when=...), and nothing says so

**What happened.** Inside a `Workflow`, `await Account.ref(context.state_id).per_workflow("Schedule follow-up sync").schedule(when=timedelta(minutes=10)).sync_poggio(context)` raised on every attempt and left the task retrying forever with backoff: `TypeError: reboot.aio.contexts.WorkflowContext is not an instance or subclass of one of the expected type(s): ['reboot.aio.contexts.TransactionContext']`. The generated client has parallel builders with different accepted contexts: `_Schedule` (`ref(id).schedule(when=...)`) takes `TransactionContext` only; `_SelfSchedule` (`self.ref().schedule(...)`) takes `WriterContext | TransactionContext`; `_Spawn` (`ref(id).spawn(when=...)`) takes `WorkflowContext | ExternalContext`, with the same `when=` argument, and auto-scopes inside a workflow. `servicer-workflow.md` classifies a scheduled workflow on another actor as a Reboot-internal call to scope with `.per_workflow(alias)` and its Quick Decision Aid names "schedule", but every example uses `schedule()` and `spawn` appears nowhere in `servicer-workflow.md`, `scheduling-basic.md` or `scheduling-recurring.md` (only in testing references, from an `ExternalContext`). mypy did not catch it: the generated methods carry `# type: ignore[misc]` and are re-exported under snake_case aliases. The app's 66 scenarios stayed green because none drove the scheduled follow-up; it surfaced only as a retrying task in the running app's log.

**Expected.** Either `_Schedule` accepts a `WorkflowContext`, or the workflow and scheduling references show `spawn(when=...)` as the in-workflow form and say `schedule(...)` is for writers and transactions. Source fix list: (1) let `_Schedule` accept a `WorkflowContext`; (2) docs in all three references (recommended immediately; the Quick Decision Aid is the line that sends a reader wrong); (3) drop the `# type: ignore[misc]`/aliases so mypy catches it.

**Repro.** Any `Workflow` that schedules delayed work on another actor via `ref(id).per_workflow(alias).schedule(when=...)`.

**Where in the skills.** `python/references/servicer-workflow.md` (Quick Decision Aid), `scheduling-basic.md`, `scheduling-recurring.md`.

**Checked at 1.6.0.** `spawn` does not appear in `servicer-workflow.md`, `scheduling-basic.md` or `scheduling-recurring.md` (grep); `scheduling-basic.md` lines ~80-88 still show `.schedule()` on any ref.
