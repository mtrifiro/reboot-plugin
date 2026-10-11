---
id: reboot-crm-64
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P3.32"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - python/references/servicer-workflow.md
  - python/references/stdlib-queue.md
tags: [negative-space, error-text]
cluster: "4.4"
still_applies: yes
status: Resolved
resolved_by: "python/references/servicer-workflow-wait.md § Never"
---

# Inside one until, a second try_dequeue on the same queue is refused without an idempotency alias

**What happened.** The `until` callable took a placeholder off a lane, filtered it out, and returned `False` because nothing real was left. `until` re-ran the callable, which called `try_dequeue` on the same queue a second time and was refused: "To call 'rbt.std.collections.queue.v1.QueueMethods.TryDequeue' of '<id>' more than once using the same context an idempotency alias or key must be specified". The loop crashed; 72 of 75 test failures that run were this one error, each surfacing as a brief that never arrived. Workaround: the callable reads a lane only when its `empty` says it holds something, returns whatever it took (placeholder included), and the placeholder is dropped after `until` returns.

**Expected.** Either `until`'s retries each get their own idempotency scope (the stdlib's own `dequeue` makes exactly one such call per attempt, so never meets this), or the `until` reference says a callable that mutates must not call the same method twice across attempts.

**Repro.** Not recorded.

**Where in the skills.** `python/references/servicer-workflow.md` (`until`).

**Checked at 1.6.0.** `python/references/servicer-workflow.md` `until` sections (~lines 1091, 1201) were grepped for alias/twice warnings about mutating callables and none found.
