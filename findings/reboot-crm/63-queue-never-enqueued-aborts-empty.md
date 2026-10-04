---
id: reboot-crm-63
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P3.31"
reboot_version: 1.6.0
severity: red
target: plugin
names:
  - python/references/stdlib-queue.md
tags: [negative-space, error-text]
cluster: "4.1"
still_applies: yes
status: Open
resolved_by: ""
---

# A Queue that has never been enqueued to aborts StateNotConstructed on empty

**What happened.** A research loop called `Queue.ref(lane).empty(context)` on a lane nobody had used. It aborted `StateNotConstructed`; the workflow failed and retried after backoff forever, and every brief waiting on the other lane stayed queued. `try_dequeue` on the same queue returns an empty response (it checks `sorted_map_id == ""`), and `empty` checks the same field, but the call never reaches it because the `Queue` actor does not exist until its first `enqueue`. Workaround: the loop enqueues one placeholder item per lane (`per_workflow`) at start and drops it after taking.

**Expected.** `empty` on a queue nobody has written to answers `True`, as its own body is written to; or `stdlib-queue.md` says a queue must be enqueued to before it is read.

**Repro.** In a workflow: `await Queue.ref(str(uuid4())).empty(context)`.

**Where in the skills.** `python/references/stdlib-queue.md`.

**Checked at 1.6.0.** `python/references/stdlib-queue.md` (lines ~39-40, 131) describes `empty` and `try_dequeue` without saying a never-enqueued queue aborts.
