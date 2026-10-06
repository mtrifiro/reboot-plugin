---
id: encore-02
project: encore
source: "v 1.4.1 Reboot/encore/docs/reboot-learnings 02.md §2"
reboot_version: 1.4.0
severity: unrated
target: plugin
names:
  - python/references/servicer-workflow-calls.md
tags: [error-text]
cluster: ""
still_applies: no
status: Resolved
resolved_by: "python/references/servicer-workflow-calls.md § Never"
---

# A second inline read in one workflow needs its own alias, and the failure retries forever

**What happened.** A second bare `await Service.ref().read(context)` in the same workflow raises `ValueError: To call inline reader ... more than once using the same context an idempotency alias or key must be specified`. Because it is an undeclared error the workflow retries forever: the rival bots spun on it silently, and only the task-dispatcher WARNING log gave it away. Fix: scope every inline read explicitly when there is more than one, e.g. `.per_workflow("Read persona")`, `.per_iteration("Read self")`.

**Expected.** Not recorded.

**Repro.** Two bare inline `read(context)` calls on the same ref inside one workflow.

**Where in the skills.** Not recorded. Related: theater-network-04 (same error text, from `initialize` seeding loops) and reboot-crm-64 (second `try_dequeue` inside one `until`).

**Checked at 1.6.0.** `python/references/servicer-workflow-calls.md` § Never: "Calling the same method on the same actor twice with a bare `.per_workflow()` / `.per_iteration()` — the auto key collides; give each its own alias", and its errors table lists `more than once using the same context an idempotency alias or key must be specified`. `servicer-workflow-exit.md` says an undeclared exception retries the workflow forever. Neither names inline `read()` specifically, nor that the only visible symptom is a dispatcher WARNING.
