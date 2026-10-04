---
id: actor-flight-01
project: actor-flight
source: "reboot-findings.md §1"
reboot_version: 1.5.0
severity: unrated
target: plugin
names:
  - python/references/servicer-workflow.md
tags: [contradiction, error-text, negative-space]
cluster: "4.1"
still_applies: yes
status: Open
resolved_by: ""
---

# A workflow cannot schedule a workflow, though the reference says it can

**What happened.** `servicer-workflow.md` classifies 'scheduled workflow on another (or this) actor' as a Reboot-internal call a workflow may make with `.per_workflow(alias)`. Calling `await CallGraph.ref(ID).per_workflow("Next refresh").schedule(when=timedelta(seconds=5)).refresh(context)` with a `WorkflowContext` fails inside the generated stub with `TypeError: reboot.aio.contexts.WorkflowContext is not an instance or subclass of one of the expected type(s): ['reboot.aio.contexts.TransactionContext']`, and the dispatcher retries the task every few seconds forever (44 tracebacks before the fix). Workaround: an app-internal `Writer` (`schedule_refresh`) that does `self.ref().schedule(...)`, called by the workflow.

**Expected.** Either the generated assertion admits `WorkflowContext`, or the reference shows this writer shape for a self-rescheduling workflow.

**Repro.** As in the code above: a workflow method calling `.per_workflow(alias).schedule(when=...).<workflow>(context)` on a ref.

**Where in the skills.** `servicer-workflow.md` call-classification table.

**Checked at 1.6.0.** python/references/servicer-workflow.md:190 still lists 'scheduled workflow on another (or this) actor' as a Reboot-internal call using `.per_workflow(alias)`; no mention of the `TransactionContext` requirement or the writer workaround.
